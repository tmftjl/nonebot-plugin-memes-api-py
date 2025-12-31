import hashlib
from datetime import datetime, timedelta, timezone
from itertools import chain

from nonebot.matcher import Matcher
from nonebot_plugin_alconna import Image, Text, on_alconna
from nonebot_plugin_localstore import get_cache_dir
from nonebot_plugin_uninfo import Uninfo
from pypinyin import Style, pinyin

from ..config import memes_config
from ..manager import meme_manager
from ..recorder import SessionIdType, get_meme_generation_keys
from ..request import MemeKeyWithProperties, render_meme_list
from .utils import UserId

memes_cache_dir = get_cache_dir("nonebot_plugin_memes_api")

help_matcher = on_alconna(
    "表情包制作",
    aliases={"表情列表", "头像表情包", "文字表情包"},
    block=True,
    priority=11,
    use_cmd_start=True,
)

usage_help_matcher = on_alconna(
    "表情帮助",
    block=True,
    priority=11,
    use_cmd_start=True,
)


@help_matcher.handle()
async def _(user_id: UserId, session: Uninfo):
    memes = meme_manager.get_memes()
    list_image_config = memes_config.memes_list_image_config

    sort_by = list_image_config.sort_by
    sort_reverse = list_image_config.sort_reverse
    if sort_by == "key":
        memes = sorted(memes, key=lambda meme: meme.key, reverse=sort_reverse)
    elif sort_by == "keywords":
        memes = sorted(
            memes,
            key=lambda meme: "".join(
                chain.from_iterable(pinyin(meme.keywords[0], style=Style.TONE3))
            ),
            reverse=sort_reverse,
        )
    elif sort_by == "date_created":
        memes = sorted(memes, key=lambda meme: meme.date_created, reverse=sort_reverse)
    elif sort_by == "date_modified":
        memes = sorted(memes, key=lambda meme: meme.date_modified, reverse=sort_reverse)

    label_new_timedelta = list_image_config.label_new_timedelta
    label_hot_threshold = list_image_config.label_hot_threshold
    label_hot_days = list_image_config.label_hot_days

    meme_generation_keys = await get_meme_generation_keys(
        session,
        SessionIdType.GLOBAL,
        time_start=datetime.now(timezone.utc) - timedelta(days=label_hot_days),
    )

    meme_list: list[MemeKeyWithProperties] = []
    for meme in memes:
        labels = []
        if datetime.now() - meme.date_created < label_new_timedelta:
            labels.append("new")
        if meme_generation_keys.count(meme.key) >= label_hot_threshold:
            labels.append("hot")
        disabled = not meme_manager.check(user_id, meme.key)
        meme_list.append(
            MemeKeyWithProperties(meme_key=meme.key, disabled=disabled, labels=labels)
        )

    # cache rendered meme list
    meme_list_hashable = [
        (
            {
                "key": meme.key,
                "keywords": meme.keywords,
                "shortcuts": [
                    shortcut.humanized or shortcut.key for shortcut in meme.shortcuts
                ],
                "tags": sorted(meme.tags),
            },
            prop,
        )
        for meme, prop in zip(memes, meme_list)
    ]
    meme_list_hash = hashlib.md5(str(meme_list_hashable).encode("utf8")).hexdigest()
    meme_list_cache_file = memes_cache_dir / f"{meme_list_hash}.jpg"
    if not meme_list_cache_file.exists():
        img = await render_meme_list(
            meme_list,
            text_template=list_image_config.text_template,
            add_category_icon=list_image_config.add_category_icon,
        )
        with open(meme_list_cache_file, "wb") as f:
            f.write(img)
    else:
        img = meme_list_cache_file.read_bytes()

    msg = Text(
        f"触发方式：关键词{memes_config.memes_command_prefixes} 表情名 图片/文字/@某人\n"
        f"例：{memes_config.memes_command_prefixes[0]}卡提举牌 抽我\n"
        "发送"表情详情+关键词"查看预览\n"
        "群管可 禁用/启动表情+表情名\n"
        "目前支持的表情列表："
    ) + Image(raw=img)
    await msg.send()


@usage_help_matcher.handle()
async def _(matcher: Matcher):
    memes_prefix = memes_config.memes_command_prefixes[0] if memes_config.memes_command_prefixes else ""

    help_text = (
        "- 表情列表\n"
        "发送 “表情包制作” 查看表情列表\n"
        "- 表情详情\n"
        "发送 “表情详情 + 表情名/关键词” 查看表情详细信息和表情预览\n"
        "- 表情搜索\n"
        "发送 “表情搜索 + 关键词” 查找相关的表情\n"
        "- 表情包开关\n"
        "- “超级用户” 和 “管理员” 可以启用或禁用某些表情包\n"
        "发送 启用表情/禁用表情 表情名/关键词，如：禁用表情 摸\n"
        "- “超级用户” 可以设置某个表情包的管控模式（黑名单/白名单）\n"
        "发送 全局启用表情 表情名/关键词 可将表情设为黑名单模式；\n"
        "发送 全局禁用表情 表情名/关键词 可将表情设为白名单模式；\n"
        "- 白名单保护（仅超级用户）\n"
        "发送 “添加保护@用户” 或 “添加保护<QQ号>” 添加保护白名单\n"
        "发送 “移除保护@用户” 或 “移除保护<QQ号>” 移除保护白名单\n"
        "发送 “保护表情<表情名>” 添加保护表情\n"
        "发送 “取消保护表情<表情名>” 移除保护表情\n"
        "发送 “保护列表” 查看保护配置\n"
        "- 表情使用\n"
        f"发送 “{memes_prefix}关键词 + 图片/文字” 制作表情\n"
        "可使用 “自己”、“@某人” 获取指定用户的头像作为图片\n"
        "可使用 “@ + 用户id” 指定任意用户获取头像，如 “摸 @114514”\n"
        "可将回复中的消息作为文字和图片的输入\n"
        "- 随机表情\n"
        "发送 “随机表情 + 图片/文字” 可随机制作表情\n"
        "随机范围为 图片/文字 数量符合要求的表情\n"
        "- 表情调用统计\n"
        "发送 “[我的][全局]<时间段>表情调用统计 [表情名]” 获取表情调用次数统计图\n"
        "“我的”、“全局”、<时间段>、“表情名” 均为可选项\n"
        "<时间段> 的关键词有：日、本日、周、本周、月、本月、年、本年\n"
        "如：“我的今日表情调用统计 petpet”"
    )

    await matcher.finish(help_text)
