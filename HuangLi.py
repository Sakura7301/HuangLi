import json  
import plugins  
import requests  
from typing import Optional  
from datetime import datetime  
from config import conf 
from bridge.context import ContextType  
from bridge.reply import Reply, ReplyType  
from common.log import logger 
from plugins import *  


@plugins.register(  
    name="HuangLi",  # 插件名称  
    desire_priority=99,  # 插件优先级  
    hidden=False,  # 是否隐藏  
    desc="黄历",  # 插件描述  
    version="1.0",  # 插件版本  
    author="sakura7301",  # 作者  
)  
class HuangLi(Plugin):  
    def __init__(self: str):  
        super().__init__()  # 调用父类的初始化
        # 初始化插件配置
        self.base_url = "https://api.tanshuapi.com/api/almanac/v1/index"    
        # 获取探数API
        self.api_key = conf().get("tan_shu_api_key")
        # 注册处理上下文的事件  
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context  
        logger.info("[HuangLi] 插件初始化完毕")
    
    def get_almanac(self, year: Optional[str] = None,   
                    month: Optional[str] = None,   
                    day: Optional[str] = None) -> dict:  
        """  
        获取老黄历数据  
        """  
        # 构建请求参数  
        params = {'key': self.api_key}  
        
        # 添加可选参数（进行验证）  
        if year:  
            try:  
                year_int = int(year)  
                if not 1900 <= year_int <= 2100:  
                    logger.error("年份必须在1900-2100之间")  
                    return None  
                params['year'] = str(year_int)  
            except ValueError:  
                logger.error("年份必须是有效的数字")  
                return None  
                
        if month:  
            try:  
                month_int = int(month)  
                if not 1 <= month_int <= 12:  
                    logger.error("月份必须在1-12之间")  
                    return None  
                params['month'] = str(month_int).zfill(2)  
            except ValueError:  
                logger.error("月份必须是有效的数字")  
                return None  
                
        if day:  
            try:  
                day_int = int(day)  
                if not 1 <= day_int <= 31:  
                    logger.error("日期必须在1-31之间")  
                    return None  
                params['day'] = str(day_int).zfill(2)  
            except ValueError:  
                logger.error("日期必须是有效的数字")  
                return None  
        
        # 打印请求信息（隐藏完整key）  
        logger.debug("\n=== 请求信息 ===")  
        logger.debug(f"请求URL: {self.base_url}")  
        safe_params = params.copy()  
        if 'key' in safe_params:  
            key = safe_params['key']  
            safe_params['key'] = f"{key[:4]}...{key[-4:]}"  
        logger.debug(f"请求参数: {safe_params}")  
        
        try:  
            # 发送请求  
            logger.debug("\n正在发送请求...")  
            response = requests.get(self.base_url, params=params, timeout=10)  
            response.raise_for_status()  # 检查HTTP状态码  
            
            # 尝试解析JSON  
            data = response.json()  
            
            # 验证响应数据  
            if not isinstance(data, (dict, list)):  
                logger.error("API响应格式错误")  
                return None  
            
            if data:  
                if 'data' in data:  
                    return data['data']  
                else:  
                    logger.error("没有'data'字段！")  
                    return None  
            else:  
                logger.error("data is None!")  
                return None  
            
        except requests.exceptions.Timeout:  
            logger.error("请求超时,请稍后重试")  
            return None  
        except requests.exceptions.HTTPError as e:  
            logger.error(f"HTTP错误: {e.response.status_code}")  
            return None  
        except requests.exceptions.RequestException as e:  
            logger.error(f"请求失败: {str(e)}")  
            return None  
        except json.JSONDecodeError:  
            logger.error("API返回的数据不是有效的JSON格式")  
            return None  
        except Exception as e:  
            logger.error(f"未知错误: {str(e)}")  
            return None  

    def format_almanac(self, data: dict) -> str:  
        """  
        格式化老黄历数据为纯文本格式  
        """  
        try:    
            if not isinstance(data, dict):   
                logger.error("输入不是字典！")   
                return None   
            
            # 构建输出文本  
            sections = f"""公历：{data['solar_calendar']}\n农历：{data['lunar_calendar']}\n星期：{data['week']} ({data['en_week']})\n{data['year_of'][0]} {data['year_of'][1]} {data['year_of'][2]}\n五行：{data['five_elements']}\n冲煞：{data['conflict']}\n宜：{'、'.join(data['should'])}\n忌：{'、'.join(data['avoid'])}\n吉神宜趋：{data['lucky_god']}\n财神方位：{data['wealthy_god']}\n喜神方位：{data['happy_god']}\n福神方位：{data['bless_god']}\n煞位：{data['evil']}\n胎神：{data['fetal_god']}\n吉日：{data['auspicious_day']}"""  
            return sections  
            
        except Exception as e:  
            return f"格式化数据失败: {str(e)}"  

    def HuangLiRquest(self, query: str) -> bool:  
        """检查请求关键词"""  
        divination_keywords = ['黄历', '老黄历', '今日黄历']  
        return any(keyword in query for keyword in divination_keywords)

    def HuangLi(self):  
        """使用示例"""  
        try:      
            # 获取当前日期  
            today = datetime.now()  
            
            # 查询老黄历  
            data = self.get_almanac(
                year=str(today.year),  
                month=str(today.month),  
                day=str(today.day)  
            )  
            
            if data:
                # 格式化并显示结果  
                return self.format_almanac(data) 
            else:
                return None
            
        except Exception as e:  
            logger.error(f"未知错误: {str(e)}")  

    def on_handle_context(self, e_context: EventContext):  
        """处理上下文事件"""  
        if e_context["context"].type not in [ContextType.TEXT]:  
            logger.debug("[HuangLi] 上下文类型不是文本，无需处理")  
            return  
        
        content = e_context["context"].content.strip()  
        logger.debug(f"[HuangLi] 处理上下文内容: {content}")  

        if self.HuangLiRquest(content):
            logger.info("[HuangLi] 黄历")
            reply = Reply()
            reply.content = self.HuangLi()
            reply.type = ReplyType.TEXT
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑 


    def get_help_text(self, **kwargs):  
        """获取帮助文本"""  
        help_text = "输入'黄历'可得获得黄历推送哦~🐾\n"  
        return help_text

