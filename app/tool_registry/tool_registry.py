# # --- Tool Registry ---
# from functions.search_research_papers import search_research_papers

# TOOL_REGISTRY = {
#     "search_research_papers": search_research_papers

#     # Add new tools here as needed
# }

from app.functions.search_research_papers import search_research_papers


class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name: str, func):
        self.tools[name] = func

    def execute(self, name: str, **kwargs):
        print("TOOL CALLED:", name)  # DEBUG LINE
        print("WITH ARGS:", kwargs)  # DEBUG LINE
        print("AVAILABLE TOOLS:", list(self.tools.keys()))  # DEBUG LINE
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        return self.tools[name](**kwargs)


# -----------------------------
# GLOBAL REGISTRY INSTANCE
# -----------------------------
registry = ToolRegistry()

registry.register(
    "search_research_papers",
    search_research_papers
)
