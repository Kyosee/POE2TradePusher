import asyncio
import time
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
from DrissionPage import ChromiumOptions, ChromiumPage
from DrissionPage.errors import ElementNotFoundError
from utils.RecaptchaSolver import RecaptchaSolver


def print_with_time(message):
    """打印带时间的日志信息"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")


class AccountVerifier:
    """账号验证器，用于验证POE账号信息"""
    
    # 账号状态常量
    STATUS_PENDING = "待刷新"
    STATUS_PROCESSING = "刷新中"
    STATUS_SUCCESS = "已刷新"  # 修改为"已刷新"
    STATUS_FAILED = "失败"
    
    # 封禁状态常量
    BANNED_UNKNOWN = "待获取"
    BANNED_YES = "是"
    BANNED_NO = "否"
    
    def __init__(self, logger=None):
        """初始化账号验证器
        
        Args:
            logger: 日志记录器，需要有info和error方法
        """
        self.logger = logger or self._default_logger()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        self.login_url = "https://www.pathofexile.com/login"
        self.account_url = "https://www.pathofexile.com/my-account"
        
    def _default_logger(self):
        """创建默认日志记录器"""
        class DefaultLogger:
            def info(self, msg): print_with_time(f"[INFO] {msg}")
            def error(self, msg): print_with_time(f"[ERROR] {msg}")
            def warning(self, msg): print_with_time(f"[WARNING] {msg}")
        return DefaultLogger()
    
    async def solve_turnstile(self, page):
        """解决Cloudflare验证
        
        Args:
            page: DrissionPage对象
            
        Returns:
            bool: 是否成功解决验证
        """
        self.logger.info('等待Cloudflare验证加载')
        await asyncio.sleep(2)  # 确保页面完全加载
        
        # 确保debug目录存在
        import os
        if not os.path.exists('debug'):
            os.makedirs('debug')
            
        # 查找所有div元素
        divs = page.eles('tag:div', timeout=11)
        self.logger.info('查找Cloudflare iframe')
            
        iframe = None
        for div in divs:
            if div.shadow_root:
                try:
                    iframe = div.shadow_root.ele(
                        "xpath://iframe[starts-with(@src, 'https://challenges.cloudflare.com/')]",
                        timeout=11
                    )
                    if iframe:
                        break
                except ElementNotFoundError:
                    continue
        
        if not iframe:
            self.logger.error("未找到Cloudflare iframe，可能页面结构已变化")
            return False
        
        self.logger.info("找到iframe，等待加载body")
        body_element = iframe.ele('tag:body', timeout=115).shadow_root
        
        # 尝试多种文本匹配方式查找验证元素
        verify_element = None
        try:
            verify_element = body_element.ele("text:确认您是真人", timeout=110)
        except ElementNotFoundError:
            try:
                verify_element = body_element.ele("text:I am human", timeout=6)
            except ElementNotFoundError:
                try:
                    verify_element = body_element.ele("xpath://div[contains(@class, 'check')]|//label[contains(@class, 'check')]", timeout=6)
                except ElementNotFoundError:
                    try:
                        verify_element = body_element.ele("xpath://div[@role='button']|//button|//div[@tabindex='0']", timeout=6)
                    except ElementNotFoundError:
                        pass
        
        if not verify_element:
            self.logger.error("未找到验证元素，可能Cloudflare已更改界面")
            # 尝试截图保存当前页面状态
            try:
                page.get_screenshot('debug/cloudflare_challenge.png')
            except Exception as e:
                self.logger.error(f'保存截图失败: {str(e)}')
            return False
        
        self.logger.info(f'找到验证元素: {verify_element}')
        self.logger.info('等待元素完全加载')
        await asyncio.sleep(3)  # 增加等待时间
        
        # 尝试多种点击方法
        click_methods = [
            lambda: verify_element.click(by_js=None),  # 默认点击
            lambda: page.run_js('arguments[0].click();', verify_element),  # 直接JS点击
            lambda: page.run_js('arguments[0].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true, view: window}));', verify_element),  # 模拟鼠标事件
            lambda: verify_element.click(offset_x=5, offset_y=5)  # 使用偏移点击
        ]
        
        success = False
        for i, click_method in enumerate(click_methods):
            try:
                self.logger.info(f'尝试点击方法 {i+1}')
                click_method()
                self.logger.info(f'点击方法 {i+1} 执行成功')
                success = True
                break
            except Exception as e:
                self.logger.error(f'点击方法 {i+1} 失败: {str(e)}')
                await asyncio.sleep(1)
        
        if not success:
            self.logger.error("所有点击方法均失败")
            return False
        
        self.logger.info('等待验证完成')
        await asyncio.sleep(5)  # 等待验证完成
        
        return True
    
    async def solve_recaptcha(self, page, account):
        """解决reCAPTCHA验证
        
        Args:
            page: DrissionPage对象
            
        Returns:
            bool: 是否成功解决验证
        """
        self.logger.info('检查是否存在reCAPTCHA验证')
        
        # 确保debug目录存在
        import os
        if not os.path.exists('debug'):
            os.makedirs('debug')
        
        # 尝试查找reCAPTCHA iframe
        try:
            # 常见的reCAPTCHA iframe查找方式
            recaptcha_iframe = page.ele('xpath://iframe[contains(@src, "recaptcha") or contains(@title, "recaptcha")]', timeout=13)
            if not recaptcha_iframe:
                # 如果没有找到iframe，检查是否有其他验证元素
                recaptcha_div = page.ele('xpath://div[contains(@class, "g-recaptcha") or contains(@class, "recaptcha")]', timeout=12)
                if not recaptcha_div:
                    self.logger.info('未检测到reCAPTCHA验证')
                    return True  # 没有验证需要解决
                
                self.logger.info('找到reCAPTCHA div元素，但未找到iframe')
            else:
                self.logger.info('找到reCAPTCHA iframe')
                
            # 截图保存验证状态
            try:
                page.get_screenshot('debug/recaptcha_detected.png')
            except Exception as e:
                self.logger.error(f'保存截图失败: {str(e)}')
            
            # 尝试切换到iframe并点击复选框
            if recaptcha_iframe:
                self.logger.info('切换到reCAPTCHA iframe')
                try:
                    recaptchaSolver = RecaptchaSolver(page)
                    recaptchaSolver.solveCaptcha()
                    self.logger.info(f'reCAPTCHA处理完成')
                except Exception as e:
                    self.logger.info(f'reCAPTCHA处理完成{str(e)}')
                
                await asyncio.sleep(3)
                    
                # 检查验证是否完成
                try:
                    # 尝试再次点击登录按钮
                    login_button = page.ele("@class=sign-in__submit", timeout=6)
                    password_input = page.ele("@name=login_password", timeout=6)
                    if login_button:
                        password = account.get('password', '')
                        # 填写登录信息
                        password_input.click()
                        password_input.input(password)
                        await asyncio.sleep(2)
                        
                        self.logger.info('验证后再次点击登录按钮')
                        login_button.click()
                        
                        # 增加二次验证检查
                        await asyncio.sleep(5)
                        try:
                            # 检查是否再次出现验证
                            second_recaptcha = page.ele('xpath://div[contains(@class, "g-recaptcha") or contains(@class, "recaptcha")] | //iframe[contains(@src, "recaptcha")]', timeout=8)
                            if second_recaptcha:
                                self.logger.info("检测到二次reCAPTCHA验证，尝试再次解决...")
                                # 递归调用自身处理二次验证
                                return await self.solve_recaptcha(page, account)
                        except ElementNotFoundError:
                            pass
                        
                        return True
                except ElementNotFoundError:
                    # 如果找不到登录按钮，可能已经登录成功
                    self.logger.info('验证后未找到登录按钮，可能已经登录成功')
                    return True
            else:
                # 尝试直接点击验证区域
                try:
                    recaptcha_div.click()
                    self.logger.info('点击reCAPTCHA区域')
                    await asyncio.sleep(5)
                    return True
                except Exception as e:
                    self.logger.error(f'点击reCAPTCHA区域失败: {str(e)}')
            
            self.logger.error('无法完成reCAPTCHA验证')
            return False
        except Exception as e:
            self.logger.error(f'处理reCAPTCHA验证时发生异常: {str(e)}')
            return False
    
    def update_account_info(self, account, username=None, poesessid=None, banned=None):
        """更新账号信息
        
        Args:
            account: 账号信息字典
            username: 用户名，如果为None则不更新
            poesessid: POESESSID cookie，如果为None则不更新
            banned: 是否被封禁，如果为None则不更新
        """
        current_username = account.get('username')
        current_poesessid = account.get('poesessid')
        email = account.get('email', '')
        
        # 更新用户名
        if username is not None and (not current_username or username != current_username):
            self.logger.info(f"账号 {email} 用户名已更新: {username}")
            account['username'] = username
        
        # 更新POESESSID
        if poesessid is not None and poesessid != current_poesessid:
            self.logger.info(f"账号 {email} POESESSID已更新")
            account['poesessid'] = poesessid
        
        # 更新封禁状态
        if banned is not None:
            banned_value = 1 if banned else 0
            account['banned'] = banned_value
            
        # 更新刷新日期
        account['refresh_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新状态为已刷新(成功)
        account['status'] = self.STATUS_SUCCESS

    async def check_account_status(self, page, account):
        """检查账号状态 - A1流程
        
        Args:
            page: DrissionPage对象
            account: 账号信息字典
            
        Returns:
            tuple: (是否登录成功, 用户名, POESESSID, 是否被封禁)
        """
        self.logger.info("访问账号页面检查状态")
        # 访问账号页面
        page.get(self.account_url)
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 检查是否需要处理Cloudflare验证
        if "403 Forbidden" in page.title or "请稍候…" in page.title:
            self.logger.info("检测到Cloudflare验证页面，尝试解决...")
            solved = await self.solve_turnstile(page)
            if not solved:
                return False, None, None, None
            # 验证成功后重新加载页面
            page.get(self.account_url)
            await asyncio.sleep(3)
        
        # 获取页面内容
        page_text = page.html
        
        # 检查是否登录成功 - 查找"Log Out"字样
        logged_in = "Log Out" in page_text
        
        if not logged_in:
            self.logger.info("未找到'Log Out'字样，未登录状态")
            return False, None, None, None
        
        # 获取POESESSID cookie
        poesessid = None
        cookies = page.cookies()
        for cookie in cookies:
            if (cookie.get('name') == 'POESESSID'):
                poesessid = cookie.get('value')
                break
                
        # 检查是否被封禁
        banned = "(Banned)" in page_text
        if banned:
            self.logger.warning(f"账号 {account.get('email', '')} 已被封禁")
            
        # 尝试获取用户名
        username = None
        try:
            # 先尝试从状态元素获取
            try:
                status_element = page.ele("@class=statusItem loggedInStatus", timeout=10)
                if status_element:
                    username_element = status_element.ele("tag:a")
                    username = username_element.text if username_element else None
            except ElementNotFoundError:
                pass
                
            # 如果状态元素中没找到，尝试从页面标题提取
            if not username and "My Account" in page.title:
                title_parts = page.title.split('-')
                if len(title_parts) > 1:
                    username_part = title_parts[1].strip()
                    username = username_part.replace('(Banned)', '').strip()
        except Exception as e:
            self.logger.error(f"获取用户名时出错: {str(e)}")
        
        return True, username, poesessid, banned
    
    async def login_account(self, page, account):
        """登录账号 - B1流程
        
        Args:
            page: DrissionPage对象
            account: 账号信息字典
            
        Returns:
            bool: 是否登录成功
        """
        email = account.get('email', '')
        password = account.get('password', '')
        
        self.logger.info(f"开始登录账号: {email}")
        
        # 访问登录页面
        page.get(self.login_url)
        
        # 等待页面加载
        await asyncio.sleep(2)
        
        # 检查是否需要处理Cloudflare验证
        if "403 Forbidden" in page.title or "请稍候…" in page.title:
            self.logger.info("检测到Cloudflare验证页面，尝试解决...")
            solved = await self.solve_turnstile(page)
            if not solved:
                return False
            # 验证成功后重新加载页面
            page.get(self.login_url)
            await asyncio.sleep(2)
        
        # 等待登录表单加载
        self.logger.info("等待登录表单加载")
        try:
            email_input = page.ele("@name=login_email", timeout=110)
            password_input = page.ele("@name=login_password", timeout=6)
            login_button = page.ele("@class=sign-in__submit", timeout=6)
        except ElementNotFoundError as e:
            self.logger.error(f"找不到登录表单元素: {str(e)}")
            return False
        
        # 填写登录信息
        self.logger.info("填写登录信息")
        email_input.click()
        email_input.input(email)
        await asyncio.sleep(0.5)
        password_input.click()
        password_input.input(password)
        
        # 点击登录按钮
        self.logger.info("点击登录按钮")
        login_button.click()
        
        # 等待登录完成
        self.logger.info("等待登录完成")
        await asyncio.sleep(5)
        
        # 检查是否需要处理reCAPTCHA验证
        try:
            recaptcha_exists = page.ele('xpath://div[contains(@class, "g-recaptcha") or contains(@class, "recaptcha")] | //iframe[contains(@src, "recaptcha")]', timeout=12)
            if recaptcha_exists:
                self.logger.info("检测到reCAPTCHA验证，尝试解决...")
                solved = await self.solve_recaptcha(page, account=account)
                if not solved:
                    return False
                # 验证成功后等待页面加载
                await asyncio.sleep(5)
        except Exception as e:
            self.logger.error(f"检查reCAPTCHA时发生异常: {str(e)}")
        
        # 检查是否有错误消息
        try:
            error_element = page.ele("@class=error-message", timeout=6)
            error_message = error_element.text
            self.logger.error(f"账号 {email} 登录失败: {error_message}")
            return False
        except ElementNotFoundError:
            # 检查是否有"Log Out"字样
            if "Log Out" in page.html:
                self.logger.info(f"账号 {email} 登录成功")
                return True
            else:
                # 没有错误消息，但也没有登录成功标志
                self.logger.info(f"账号 {email} 登录状态不明确，尝试访问账号页面进一步确认")
                return True  # 返回True并让后续流程进一步确认
    
    async def verify_account(self, account):
        """验证单个账号
        
        Args:
            account: 账号信息字典，包含email和password字段
            
        Returns:
            tuple: (账号邮箱, 状态, 用户名, POESESSID cookie)
        """
        email = account.get('email', '')
        password = account.get('password', '')
        current_poesessid = account.get('poesessid')
        current_username = account.get('username')
        
        if not email or not password:
            return email, self.STATUS_FAILED, None, None
        
        self.logger.info(f"开始验证账号: {email}")
        
        # 更新账号状态为处理中
        account['status'] = self.STATUS_PROCESSING
        
        # 创建浏览器选项
        options = (
            ChromiumOptions()
            .set_user_data_path(path="data/"+email)
            .headless()
            .incognito()
            .auto_port(True)
            .set_timeouts(base=1)
            .set_user_agent(self.user_agent)
            # .set_argument('--no-sandbox')
            # .set_argument('--disable-gpu')
        )
        
        # 创建页面对象
        page = ChromiumPage(options)
        
        try:
            # 记录页面对象到浏览器进程列表（如果有传递）
            if hasattr(self, 'browser_processes') and self.browser_processes is not None:
                self.browser_processes.append(page)
            
            # 检查账号信息中是否包含POESESSID - 路径1
            if current_poesessid:
                self.logger.info(f"账号 {email} 已有POESESSID，尝试直接访问账号页面")
                cookies = f'POESESSID={current_poesessid};domain=.pathofexile.com;'
                page.set.cookies(cookies)
                
                # 执行A1流程 - 检查账号状态
                logged_in, username, poesessid, banned = await self.check_account_status(page, account)
                
                if logged_in:
                    # 更新账号信息
                    self.update_account_info(account, username, poesessid, banned)
                    
                    # 不再添加额外字样，直接返回标准状态
                    return email, self.STATUS_SUCCESS, username, poesessid
                else:
                    self.logger.info(f"账号 {email} 使用现有POESESSID验证失败，尝试登录")
                    # 现有POESESSID无效，执行登录流程 - 路径2
            else:
                self.logger.info(f"账号 {email} 无POESESSID，执行登录流程")
            
            # 执行B1流程 - 登录账号
            login_success = await self.login_account(page, account)
            
            if not login_success:
                account['status'] = self.STATUS_FAILED
                return email, self.STATUS_FAILED, None, None
            
            # 登录后再次检查账号状态
            logged_in, username, poesessid, banned = await self.check_account_status(page, account)
            
            if logged_in:
                # 更新账号信息
                self.update_account_info(account, username, poesessid, banned)
                
                # 不再添加额外字样，直接返回标准状态
                return email, self.STATUS_SUCCESS, username, poesessid
            else:
                account['status'] = self.STATUS_FAILED
                return email, self.STATUS_FAILED, None, None
                
        except Exception as e:
            account['status'] = self.STATUS_FAILED
            self.logger.error(f"验证过程发生异常: {str(e)}")
            return email, self.STATUS_FAILED, None, None
        finally:
            # 关闭浏览器
            try:
                # 从浏览器进程列表中移除（如果存在）
                if hasattr(self, 'browser_processes') and self.browser_processes is not None:
                    if page in self.browser_processes:
                        self.browser_processes.remove(page)
                page.close()
            except Exception as e:
                self.logger.error(f'关闭浏览器失败: {str(e)}')
    
    def verify_accounts(self, accounts, thread_count=1, callback=None, running_flag=None, browser_processes=None):
        """验证多个账号
        
        Args:
            accounts: 账号信息列表
            thread_count: 线程数
            callback: 回调函数，接收参数(email, status, username, poesessid)
            running_flag: 运行标志对象，用于检查是否应该停止
            browser_processes: 浏览器进程列表，用于在停止时关闭浏览器
            
        Returns:
            list: 验证结果列表，每项为(email, status, username, poesessid)元组
        """
        # 保存传入的浏览器进程列表
        if browser_processes is not None:
            self.browser_processes = browser_processes
            
        self.logger.info(f"开始验证 {len(accounts)} 个账号，使用 {thread_count} 个线程")
        
        results = []
        
        # 定义线程函数 - 修改为检查运行标志
        def verify_thread(account):
            # 如果有运行标志并且已停止，则提前返回
            if running_flag and not running_flag.running:
                return account.get('email', ''), self.STATUS_PENDING, None, None
                
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.verify_account(account))
            loop.close()
            
            # 如果有运行标志并且已停止，则不调用回调
            if running_flag and not running_flag.running:
                return account.get('email', ''), self.STATUS_PENDING, None, None
                
            # 调用回调函数
            if callback:
                callback(*result)
            
            return result
        
        # 真正使用线程池并行执行验证任务，设置最大线程数
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            # 提交所有任务
            futures = []
            for account in accounts:
                # 如果有运行标志并且已停止，则不提交更多任务
                if running_flag and not running_flag.running:
                    break
                futures.append(executor.submit(verify_thread, account))
            
            # 收集结果
            for future in futures:
                # 如果有运行标志并且已停止，则中断结果收集
                if running_flag and not running_flag.running:
                    break
                    
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # 找出对应的账号
                    index = futures.index(future)
                    if index < len(accounts):
                        account = accounts[index]
                        email = account.get('email', 'unknown')
                    else:
                        email = "unknown"
                        
                    error_msg = f"{self.STATUS_FAILED}：线程异常 {str(e)}"
                    self.logger.error(f"账号 {email} 验证线程异常: {str(e)}")
                    results.append((email, error_msg, None, None))
                    
                    # 调用回调函数报告错误
                    if callback:
                        callback(email, error_msg, None, None)
        
        self.logger.info(f"完成验证 {len(results)} 个账号")
        return results