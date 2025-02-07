from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived
import random

# --- Function definitions (No Change) ---
def increase_security(security,cost,amount):
    if security + amount < 20:
        security = security + amount
        cost = cost+50*amount
    else:
        cost = cost + 50*(20-security)
        security = 20
    return security,cost

def increase_luxury(luxury,cost,amount):
    if luxury + amount < 20:
        cost = cost + 500*amount
    else:
        cost = cost + 1000*amount
    luxury = luxury + amount
    return luxury,cost

def increase_popularity(popularity,cost,amount):
    if popularity+amount < 20:
        cost = cost+10*amount
    else:
        diff = 20 - popularity
        if diff < 0:
            diff = 0
        cost = cost + 50*(amount-diff) + 20*diff
    popularity = popularity + amount
    return popularity,cost

def increase_service(service, cost ,amount):
    if service+amount < 20:
        service = service + amount
        cost = cost + 20*amount
    else:
        cost = cost + 20*(20-service)
        service = 20

    return service, cost

def increase_quality(quality, cost ,amount):
    if amount + quality < 20:
        cost = cost + 20*amount
    else:
        if quality < 20:
            diff = 20 - quality
        else:
            diff = 0
        cost = cost + 50*(amount-diff) + 20*diff
    quality = quality + amount
    return quality, cost

def calculate_customer_flow(popularity,popularity_mod,service):
    return popularity + popularity_mod + service

def food_expanse(customer_flow,standard):
    return customer_flow*standard*10

def sign(number):
    if number<0:
        return -1
    else:
        return 1

def calculate_earning(criteria,return_mod = False):
    if criteria==10 or criteria==11:
        if return_mod:
            return criteria,criteria,criteria,0,0,0
        else:
            return criteria,criteria,criteria
    else:
        mod = sum([random.randint(1,6) for i in range(abs(criteria - 10)//2)])
        exp_mod = (abs(criteria - 10)//2)*3.5
        least_mod = (abs(criteria - 10)//2)*1
        earning = mod*sign(criteria-10)*criteria
        exp_earning = (abs(criteria - 10)//2)*sign(criteria-10)*criteria*3.5
        if sign(criteria-10)<0:
                least_earning = (abs(criteria - 10)//2)*sign(criteria-10)*criteria*6
        else:
            least_earning = (abs(criteria - 10)//2)*sign(criteria-10)*criteria*1

        if return_mod:
            return earning,exp_earning,least_earning,mod,exp_mod,least_mod
        else:
            return earning,exp_earning,least_earning


def calculate_all_earning(security,luxury,popularity,service,environment,quality,return_all=True):
    earning = 0
    exp_earning = 0
    least_earning = 0
    mod = 0
    exp_mod = 0
    least_mod = 0
    count = 0
    for criteria in [security,luxury,popularity,service,environment,quality]:
       if count == 2:
           criteria_earning,criteria_exp_earning,criteria_least_earning,mod,exp_mod,least_mod = calculate_earning(criteria,True)
       else:
           criteria_earning,criteria_exp_earning,criteria_least_earning = calculate_earning(criteria,False)
       earning = earning + criteria_earning
       exp_earning = exp_earning + criteria_exp_earning
       least_earning = least_earning + least_earning
       count = count + 1
    if return_all:
        return earning,exp_earning,least_earning,mod,exp_mod,least_mod
    else:
        return earning

def increase_value(start,modifier):
    for i in range(len(start)):
        start[i]=start[i]+modifier[i]

    return start
def calculate_reward(start,modifier,standard = 2):
    cost = 0
    security,luxury,popularity,service,quality,environment = start
    security_mod,luxury_mod,popularity_mod,service_mod,quality_mod,environment_mod = modifier
    security,cost =increase_security(security,cost,security_mod)
    luxury, cost =increase_luxury(luxury,cost,luxury_mod)
    popularity,cost = increase_popularity(popularity,cost,popularity_mod)
    service,cost = increase_service(service,cost,service_mod)
    quality,cost = increase_quality(quality,cost,quality_mod)
    earning,exp_earning,least_earning,popularity_mod,exp_mod,least_mod = calculate_all_earning(security,luxury,popularity,service,environment,quality,return_all=True)
    customer_flow = calculate_customer_flow(popularity,popularity_mod,service)
    exp_flow = calculate_customer_flow(popularity,exp_mod,service)
    least_flow = calculate_customer_flow(popularity,least_mod,service)
    storage_deduct = food_expanse(customer_flow,standard)
    exp_deduct = food_expanse(exp_flow,standard)
    least_deduct = food_expanse(least_flow,standard)
    return earning,exp_earning,least_earning,storage_deduct,exp_deduct,least_deduct,cost

# --- Plugin Class with Help Function ---
@register(name="TavernSimulatorPlugin", description="丽芙酒馆营业规则模拟插件", version="1.1", author="YourName") # Updated version to 1.1
class TavernSimulatorPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        self.tavern_attributes = {
            "security": 10,
            "luxury": 22,
            "popularity": 10,
            "service": 4,
            "quality": 0,
            "environment": 18,
        }
        self.last_cost = 0
        self.last_earning_info = {}

    async def initialize(self):
        pass

    async def _handle_tavern_command(self, ctx: EventContext, command: str, args_str: str = ""):
        """处理酒馆相关命令"""
        sender_id = ctx.event.sender_id if isinstance(ctx.event, GroupNormalMessageReceived) else "user"

        if command == "查看":
            attributes_str = "\n".join([f"{name.capitalize()}: {value}" for name, value in self.tavern_attributes.items()])
            reply = f"<{sender_id}>的丽芙酒馆属性:\n{attributes_str}\n\n上次运营总投入: {self.last_cost}龙金\n上次运营收益:\n{self._format_earning_info(self.last_earning_info)}"
            ctx.add_return("reply", [reply])
        elif command == "提升":
            parts = args_str.split()
            if len(parts) != 2:
                reply = f"<{sender_id}> 命令格式错误，请使用 `.酒馆 提升 <属性> <数值>`，例如 `.酒馆 提升 安全 5`"
            else:
                attribute_name = parts[0].lower()
                amount_str = parts[1]
                if attribute_name not in self.tavern_attributes:
                    reply = f"<{sender_id}> 无效的属性名称: '{attribute_name}'，支持属性: {', '.join(self.tavern_attributes.keys())}"
                elif not amount_str.isdigit():
                    reply = f"<{sender_id}> 提升数值必须是正整数: '{amount_str}'"
                else:
                    amount = int(amount_str)
                    if amount <= 0:
                        reply = f"<{sender_id}> 提升数值必须是正整数: '{amount}'"
                    else:
                        attribute_before_upgrade = self.tavern_attributes[attribute_name]
                        cost = 0
                        if attribute_name == "security":
                            self.tavern_attributes["security"], cost = increase_security(self.tavern_attributes["security"], cost, amount)
                        elif attribute_name == "luxury":
                            self.tavern_attributes["luxury"], cost = increase_luxury(self.tavern_attributes["luxury"], cost, amount)
                        elif attribute_name == "popularity":
                            self.tavern_attributes["popularity"], cost = increase_popularity(self.tavern_attributes["popularity"], cost, amount)
                        elif attribute_name == "service":
                            self.tavern_attributes["service"], cost = increase_service(self.tavern_attributes["service"], cost, amount)
                        elif attribute_name == "quality":
                            self.tavern_attributes["quality"], cost = increase_quality(self.tavern_attributes["quality"], cost, amount)
                        elif attribute_name == "environment":
                            self.tavern_attributes["environment"] = min(self.tavern_attributes["environment"] + amount, 20)
                            cost = 0
                        else:
                            cost = 0

                        attribute_after_upgrade = self.tavern_attributes[attribute_name]

                        reply = f"<{sender_id}> 成功提升 '{attribute_name.capitalize()}' {amount} 点，花费 {cost} 龙金。\n'{attribute_name.capitalize()}' 从 {attribute_before_upgrade} 提升至 {attribute_after_upgrade}。\n当前 '{attribute_name.capitalize()}' 值为: {self.tavern_attributes[attribute_name]}"
                        if cost > 0:
                            reply += f"，总投入成本增加 {cost} 龙金。"

                ctx.add_return("reply", [reply])


        elif command == "计算":
            start_attributes = list(self.tavern_attributes.values())
            modifier = [0, 0, 0, 0, 0, 0]
            earning, exp_earning, least_earning, storage_deduct, exp_deduct, least_deduct, cost = calculate_reward(start_attributes, modifier)

            self.last_cost = cost
            self.last_earning_info = {
                "随机赚取": earning - cost,
                "期望赚取": exp_earning - cost,
                "最少赚取": least_earning - cost,
                "随机储存": storage_deduct,
                "期望储存": exp_deduct,
                "最少储存": least_deduct,
            }

            earning_reply = self._format_earning_info(self.last_earning_info)

            reply = f"<{sender_id}> 丽芙酒馆本周期运营计算结果:\n\n{earning_reply}\n总运营成本 (不含食物储存): {cost} 龙金\n食物储存成本:\n  随机: {storage_deduct} 龙金\n  期望: {exp_deduct} 龙金\n  最少: {least_deduct} 龙金"
            ctx.add_return("reply", [reply])
        elif command == "帮助" or command == "help": # Help command handling
            reply = self._format_help_message()
            ctx.add_return("reply", [reply])
        else:
            reply = f"<{sender_id}> 未知酒馆命令: '{command}'，支持命令: 查看, 提升, 计算, 帮助" # Help in unknown command message
            ctx.add_return("reply", [reply])


    def _format_earning_info(self, earning_info):
        """格式化运营收益信息为易于阅读的字符串"""
        info_lines = [
            f"随机净利润: {earning_info.get('随机赚取', 'N/A')} 龙金",
            f"期望净利润: {earning_info.get('期望赚取', 'N/A')} 龙金",
            f"最少净利润: {earning_info.get('最少赚取', 'N/A')} 龙金",
        ]
        return "\n".join(info_lines)

    def _format_help_message(self): # Help message formatting function
        """格式化帮助信息为易于阅读的字符串"""
        help_lines = [
            "**丽芙酒馆营业规则模拟插件 - 帮助信息**",
            "",
            "**命令列表:**",
            "- `.酒馆 查看` 或 `.tavern 查看`:  查看当前丽芙酒馆的各项属性值和上次运营收益信息。",
            "- `.酒馆 提升 <属性> <数值>` 或 `.tavern 提升 <属性> <数值>`: 提升指定属性，例如 `.酒馆 提升 安全 5`。 可提升属性包括: 安全, 奢华, 人气, 服务, 质量, 环境。",
            "- `.酒馆 计算` 或 `.tavern 计算`:  进行本周期酒馆运营计算，并显示收益、成本和食物储存预估。",
            "- `.酒馆 帮助` 或 `.tavern 帮助`:  显示本插件的帮助信息。",
            "",
            "**属性说明:**",
            "- **安全:**  影响酒馆安全事件发生几率。",
            "- **奢华:**  影响顾客群体和随机事件。",
            "- **人气:**  影响顾客数量，需持续投入维护。",
            "- **服务:**  影响顾客满意度和员工薪资。",
            "- **环境:**  影响顾客体验，设施完善程度。",
            "- **质量:**  影响食物原材料质量，与食物消耗量相关。",
            "",
            "**使用示例:**",
            "  `.酒馆 查看`",
            "  `.tavern 提升 奢华 10`",
            "  `.酒馆 计算`",
            "  `.tavern 帮助`",
        ]
        return "\n".join(help_lines)


    @handler(PersonNormalMessageReceived)
    async def person_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message.strip()
        if msg.startswith((".酒馆", ".tavern")):
            parts = msg.split(maxsplit=2)
            if len(parts) >= 2:
                command = parts[1]
                args_str = parts[2] if len(parts) == 3 else ""
                await self._handle_tavern_command(ctx, command, args_str)
            else:
                reply = "请使用 `.酒馆 <命令> [参数]` 或 `.tavern <命令> [参数]`，例如：`.酒馆 查看` 或 `.酒馆 提升 安全 5`"
                ctx.add_return("reply", [reply])
            ctx.prevent_default()


    @handler(GroupNormalMessageReceived)
    async def group_normal_message_received(self, ctx: EventContext):
        msg = ctx.event.text_message.strip()
        if msg.startswith((".酒馆", ".tavern")):
            parts = msg.split(maxsplit=2)
            if len(parts) >= 2:
                command = parts[1]
                args_str = parts[2] if len(parts) == 3 else ""
                await self._handle_tavern_command(ctx, command, args_str)
            else:
                reply = "请使用 `.酒馆 <命令> [参数]` 或 `.tavern <命令> [参数]`，例如：`.酒馆 查看` 或 `.酒馆 提升 安全 5`"
                ctx.add_return("reply", [reply])
            ctx.prevent_default()


    def __del__(self):
        pass