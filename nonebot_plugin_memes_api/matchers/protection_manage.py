from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import Alconna, Args, At, CommandMeta, on_alconna

from ..protection import protection_manager
from .utils import find_meme


# 添加白名单
add_whitelist_matcher = on_alconna(
    Alconna(
        "添加保护",
        Args["target", At | str],
        meta=CommandMeta(compact=True),
    ),
    block=True,
    priority=11,
    use_cmd_start=True,
    permission=SUPERUSER,
)


@add_whitelist_matcher.handle()
async def _(matcher: Matcher, target: At | str):
    if isinstance(target, At):
        user_id = target.target
    else:
        user_id = target

    if protection_manager.add_whitelist(user_id):
        await matcher.finish(f"已将 {user_id} 添加到保护白名单")
    else:
        await matcher.finish(f"{user_id} 已在白名单中")


# 移除白名单
remove_whitelist_matcher = on_alconna(
    Alconna(
        "移除保护",
        Args["target", At | str],
        meta=CommandMeta(compact=True),
    ),
    block=True,
    priority=11,
    use_cmd_start=True,
    permission=SUPERUSER,
)


@remove_whitelist_matcher.handle()
async def _(matcher: Matcher, target: At | str):
    if isinstance(target, At):
        user_id = target.target
    else:
        user_id = target

    if protection_manager.remove_whitelist(user_id):
        await matcher.finish(f"已将 {user_id} 从保护白名单移除")
    else:
        await matcher.finish(f"{user_id} 不在白名单中")


# 添加保护表情
add_protected_meme_matcher = on_alconna(
    Alconna(
        "保护表情",
        Args["meme_name", str],
        meta=CommandMeta(compact=True),
    ),
    block=True,
    priority=11,
    use_cmd_start=True,
    permission=SUPERUSER,
)


@add_protected_meme_matcher.handle()
async def _(matcher: Matcher, meme_name: str):
    meme = await find_meme(matcher, meme_name)
    if protection_manager.add_protected_meme(meme.key):
        await matcher.finish(f"表情 {meme.key} 已添加到保护列表")
    else:
        await matcher.finish(f"表情 {meme.key} 已在保护列表中")


# 移除保护表情
remove_protected_meme_matcher = on_alconna(
    Alconna(
        "取消保护表情",
        Args["meme_name", str],
        meta=CommandMeta(compact=True),
    ),
    block=True,
    priority=11,
    use_cmd_start=True,
    permission=SUPERUSER,
)


@remove_protected_meme_matcher.handle()
async def _(matcher: Matcher, meme_name: str):
    meme = await find_meme(matcher, meme_name)
    if protection_manager.remove_protected_meme(meme.key):
        await matcher.finish(f"表情 {meme.key} 已从保护列表移除")
    else:
        await matcher.finish(f"表情 {meme.key} 不在保护列表中")


# 查看保护列表
list_protection_matcher = on_alconna(
    "保护列表",
    block=True,
    priority=11,
    use_cmd_start=True,
    permission=SUPERUSER,
)


@list_protection_matcher.handle()
async def _(matcher: Matcher):
    whitelist = protection_manager.get_whitelist()
    protected_memes = protection_manager.get_protected_memes()

    msg = "【保护配置】\n"
    msg += f"\n保护白名单: {', '.join(whitelist) if whitelist else '（空）'}\n"
    msg += f"\n保护表情: {', '.join(protected_memes) if protected_memes else '（空）'}"

    await matcher.finish(msg)
