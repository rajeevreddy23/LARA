"""Services package for LARA backend orchestrator."""
def __getattr__(name):
    if name in ("LLMService", "get_llm_service"):
        from app.services import llm_service
        return getattr(llm_service, name)
    raise AttributeError(name)

__all__ = ["LLMService", "get_llm_service"]
