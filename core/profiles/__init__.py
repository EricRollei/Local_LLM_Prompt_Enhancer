"""
Platform profiles: what each target model wants from a prompt, as data.

    from core.profiles import get_library, plan_rewrite, check, RunFacts
    profile = get_library().get("flux2_dev")
    plan = plan_rewrite(profile, "a fox in snow", cache_dir=...)   # plan.system / plan.user -> your LLM call
    text, warnings = check(llm_answer, profile, plan.task)

No ComfyUI, torch or LLM dependency in this package.

(c) Eric Hiss. Dual license, see LICENSE.
"""

from .legacy import negative_prompt, to_legacy_config
from .loader import BUILTIN_PROFILE_DIR, USER_PROFILE_DIR, ProfileLibrary, get_library
from .official import MODE_AUTO, MODE_OFF, MODE_ON, MODE_REFRESH, MODES, load_official
from .rewriter import RewritePlan, RunFacts, plan_rewrite
from .schema import Profile, profile_from_dict
from .validate import check, clean_llm_output

__all__ = [
    "BUILTIN_PROFILE_DIR", "USER_PROFILE_DIR", "ProfileLibrary", "get_library",
    "MODE_AUTO", "MODE_OFF", "MODE_ON", "MODE_REFRESH", "MODES", "load_official",
    "RewritePlan", "RunFacts", "plan_rewrite",
    "Profile", "profile_from_dict",
    "check", "clean_llm_output",
    "negative_prompt", "to_legacy_config",
]
