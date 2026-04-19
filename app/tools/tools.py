# tools = [
#     {
#         "type": "function",
#         "name": "search_research_papers",
#         "description": "Search and retrieve full-text academic papers from Semantic Scholar. Returns at least N papers with full content for analysis.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "query": {
#                     "type": "string",
#                     "description": "Research query (e.g. fraud detection in banking AI)"
#                 },
#                 "min_results": {
#                     "type": "integer",
#                     "description": "Minimum number of full papers to retrieve",
#                     "default": 5
#                 }
#             },
#             "required": ["query"],
#             "additionalProperties": False
#         }
#     }
# ]


tools =  [
    {
        "type": "function",
        "function": {
            "name": "search_research_papers",
            "description": "Search academic papers and return full content",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for academic papers"
                    },
                    "min_results": {
                        "type": "integer",
                        "default": 3,
                        "description": "Minimum number of papers to retrieve"
                    }
                },
                "required": ["query"]
            }
        }
    }
]