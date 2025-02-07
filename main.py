from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived
import random

# --- 函数定义 (保持不变) ---
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

# --- 插件类 (修改后) ---
@register(name="TavernSimulatorPlugin", description="丽芙酒馆营业规则模拟插件", version="1.2", author="YourName") # 版本更新为 1.2
class TavernSimulatorPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        # 第一周初始数值 (修改初始化数值)
        self.initial_attributes = { # 保存初始属性，用于 "初始化" 命令
            "security": 20,
            "luxury": 22,
            "popularity": 100,
            "service": 100,
            "environment": 18,
            "quality": 100,
            "inventory": 2000, # 初始化库存
        }
        self.tavern_attributes = self.initial_attributes.copy() # 使用 copy() 避免直接修改 initial_attributes
        self.last_cost = 0
        self.last_earning_info = {}
        self.saved_attributes = None # 用于存档功能，初始为 None


    async def initialize(self):
        pass

    async def _handle_tavern_command(self, ctx: EventContext, command: str, args_str: str = ""):
        """处理酒馆相关命令"""
        sender_id = ctx.event.sender_id if isinstance(ctx.event, GroupNormalMessageReceived) else "user"

        if command == "查看":
            # 计算竞争力
            competitiveness = self._calculate_competitiveness() # 调用新的竞争力计算函数
            attributes_str = "\n".join([f"{name.capitalize()}: {value}" for name, value in self.tavern_attributes.items() if name != 'inventory']) #  查看时不显示库存
            reply = f"<{sender_id}>的丽芙酒馆属性:\n{attributes_str}\n竞争力: {competitiveness}\n\n当前库存: {self.tavern_attributes['inventory']} 龙金\n上次运营总投入: {self.last_cost} 龙金\n上次运营收益:\n{self._format_earning_info(self.last_earning_info)}"
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
                        elif attribute_name == "inventory": #  不允许直接提升库存，给出提示
                            reply = f"<{sender_id}> 不支持直接提升库存，库存通过运营收入补充。"
                            ctx.add_return("reply", [reply])
                            return # 提前返回，不执行后续回复代码
                        else:
                            cost = 0

                        attribute_after_upgrade = self.tavern_attributes[attribute_name]

                        reply = f"<{sender_id}> 成功提升 '{attribute_name.capitalize()}' {amount} 点，花费 {cost} 龙金。\n'{attribute_name.capitalize()}' 从 {attribute_before_upgrade} 提升至 {attribute_after_upgrade}。\n当前 '{attribute_name.capitalize()}' 值为: {self.tavern_attributes[attribute_name]}"
                        if cost > 0:
                            reply += f"，总投入成本增加 {cost} 龙金。"

                ctx.add_return("reply", [reply])


        elif command == "计算":
            start_attributes = list(self.tavern_attributes.values())[:6] #  只取前 6 个属性 (安全, 奢华, 人气, 服务, 环境, 质量) 用于计算
            modifier = [0, 0, 0, 0, 0, 0]
            earning, exp_earning, least_earning, storage_deduct, exp_deduct, least_deduct, cost = calculate_reward(start_attributes, modifier)

            customer_flow = calculate_customer_flow(self.tavern_attributes["popularity"], 0, self.tavern_attributes["service"]) # 使用当前人气和服务计算客流
            storage_deduct_actual = food_expanse(customer_flow, standard=2) # 计算实际食物消耗
            self.tavern_attributes["inventory"] -= storage_deduct_actual # 扣减库存

            if self.tavern_attributes["inventory"] < 0: # 库存耗尽
                storage_deduct_actual += self.tavern_attributes["inventory"] # 实际消耗不能为负数
                storage_deduct_actual = max(0, storage_deduct_actual) # 确保消耗不为负
                self.tavern_attributes["inventory"] = 0 # 库存归零
                self.tavern_attributes["quality"] = 0 # 质量重置为 0
                quality_reset_message = "\n**警告：库存已耗尽，质量已重置为 0！**" # 警告信息
            else:
                quality_reset_message = "" # 无警告信息

            self.last_cost = cost
            self.last_earning_info = {
                "随机净利润": earning - cost,
                "期望净利润": exp_earning - cost,
                "最少净利润": least_earning - cost,
                "随机储存": storage_deduct,
                "期望储存": exp_deduct,
                "最少储存": least_deduct,
            }

            earning_reply = self._format_earning_info(self.last_earning_info)
            competitiveness = self._calculate_competitiveness() # 计算竞争力

            reply = f"<{sender_id}> 丽芙酒馆本周期运营计算结果:\n竞争力: {competitiveness}\n\n{earning_reply}\n总运营成本 (不含食物储存): {cost} 龙金\n食物储存成本: {storage_deduct_actual} 龙金 (实际消耗，已从库存扣除){quality_reset_message}\n剩余库存: {self.tavern_attributes['inventory']} 龙金"
            ctx.add_return("reply", [reply])

        elif command == "初始化": # 初始化命令
            self.tavern_attributes = self.initial_attributes.copy() # 重置为初始属性
            self.last_cost = 0 # 重置上次成本
            self.last_earning_info = {} # 重置上次收益信息
            reply = f"<{sender_id}> 丽芙酒馆属性已重置为第一周初始值。"
            ctx.add_return("reply", [reply])

        elif command == "存档": # 存档命令 (初步实现)
            self.saved_attributes = { # 保存当前状态
                "attributes": self.tavern_attributes.copy(),
                "last_cost": self.last_cost,
                "last_earning_info": self.last_earning_info.copy(),
            }
            reply = f"<{sender_id}> 丽芙酒馆当前状态已存档。"
            ctx.add_return("reply", [reply])

        elif command == "帮助" or command == "help":
            reply = self._format_help_message()
            ctx.add_return("reply", [reply])
        else:
            reply = f"<{sender_id}> 未知酒馆命令: '{command}'，支持命令: 查看, 提升, 计算, 初始化, 存档, 帮助" #  添加 "初始化" 和 "存档" 到帮助提示
            ctx.add_return("reply", [reply])


    def _format_earning_info(self, earning_info):
        """格式化运营收益信息为易于阅读的字符串 (保持不变)"""
        info_lines = [
            f"随机净利润: {earning_info.get('随机赚取', 'N/A')} 龙金",
            f"期望净利润: {earning_info.get('期望赚取', 'N/A')} 龙金",
            f"最少净利润: {earning_info.get('最少赚取', 'N/A')} 龙金",
        ]
        return "\n".join(info_lines)

    def _format_help_message(self):
        """格式化帮助信息为易于阅读的字符串 (更新帮助信息)"""
        help_lines = [
            "**丽芙酒馆营业规则模拟插件 - 帮助信息**",
            "",
            "**命令列表:**",
            "- `.酒馆 查看` 或 `.tavern 查看`:  查看当前丽芙酒馆的各项属性值、竞争力、库存和上次运营收益信息。",
            "- `.酒馆 提升 <属性> <数值>` 或 `.tavern 提升 <属性> <数值>`: 提升指定属性，例如 `.酒馆 提升 安全 5`。 可提升属性包括: 安全, 奢华, 人气, 服务, 质量, 环境 (不支持直接提升库存)。", #  更新属性说明
            "- `.酒馆 计算` 或 `.tavern 计算`:  进行本周期酒馆运营计算，显示收益、成本、食物储存预估和实际库存消耗。 **注意：每次'计算'命令会实际扣除库存，并可能重置质量属性。**", #  添加库存消耗和质量重置警告
            "- `.酒馆 初始化` 或 `.tavern 初始化`:  将丽芙酒馆属性重置为第一周的初始值 (安全: 20, 奢华: 22, 人气: 100, 服务: 100, 环境: 18, 质量: 100, 库存: 2000)。", #  添加初始化命令说明和初始值
            "- `.酒馆 存档` 或 `.tavern 存档`:  保存当前丽芙酒馆的状态 (属性、成本、收益信息)。 **当前存档功能为初步实现，重启后存档会丢失。**", #  添加存档命令说明和警告
            "- `.酒馆 帮助` 或 `.tavern 帮助`:  显示本插件的帮助信息。",
            "",
            "**属性说明:**",
            "- **安全:**  影响酒馆安全事件发生几率。提升成本: 每点 50 龙金。",
            "- **奢华:**  影响顾客群体和随机事件。提升成本: 每点 500 龙金 (超过 20 点后每点 1000 龙金)。",
            "- **人气:**  影响顾客数量，需持续投入维护。提升成本: 每点 10 龙金 (超过 20 点后每点 50 龙金)。",
            "- **服务:**  影响顾客满意度和员工薪资。提升成本: 每点 20 龙金。",
            "- **环境:**  影响顾客体验，设施完善程度。提升无成本，上限 20 点。",
            "- **质量:**  代表原材料质量，影响食物消耗量和顾客满意度。提升成本: 每点 20 龙金 (超过 20 点后每点 50 龙金)。每周期质量依据上一周期消耗的食物总量决定数值 (库存耗尽后重置为 0)。", #  更新质量属性说明，添加库存耗尽重置质量的说明
            "- **库存:**  代表酒馆当前拥有的食物原材料，初始值为 2000 龙金。每次 '计算' 命令会根据客流消耗库存。库存耗尽后质量会重置为 0。", #  添加库存属性说明
            "- **竞争力:**  每周期的维度总和，决定运营期间的随机竞争对手事件。(计算值，不可直接提升)", # 添加竞争力说明
            "",
            "**使用示例:**",
            "  `.酒馆 查看`",
            "  `.tavern 提升 奢华 10`",
            "  `.酒馆 计算`",
            "  `.tavern 初始化`", # 添加初始化示例
            "  `.tavern 存档`", # 添加存档示例
            "  `.tavern 帮助`",
        ]
        return "\n".join(help_lines)

    def _calculate_competitiveness(self): # 新增竞争力计算函数
        """计算竞争力，即六个维度的总和"""
        attributes = self.tavern_attributes
        return sum([attributes["security"], attributes["luxury"], attributes["popularity"], attributes["service"], attributes["environment"], attributes["quality"]])


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