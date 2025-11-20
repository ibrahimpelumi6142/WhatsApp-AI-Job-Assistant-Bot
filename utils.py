def detect_intent(text: str):
    """Simple keyword-based intent detection (demo only)."""
    if any(word in text for word in ["job", "jobs", "find", "search"]):
        return "job"
    if any(word in text for word in ["cv", "resume"]):
        return "cv"
    return "default"
