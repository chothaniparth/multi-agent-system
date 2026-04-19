from agent import build_search_agent, build_reader_agent, writer_chain, critic_chain
from rich import print

def research_pipline(topic: str) -> dict:
    
    state = {}
    
    # search aget working
    print("\n" + "="*50)
    print("search agent working...")
    print("\n" + "="*50)
    
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages" : [("user", f"find recent, reliable and detailed information about: {topic}")]
    })
    state["search_result"] = search_result["messages"][-1].content
    
    print("\n search result: ", state["search_result"])
    
    #step 2: reader agent
    print("\n" + "="*50)
    print("reader agent working...")
    print("\n" + "="*50)
    
    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user", f"based on the following search results about '{topic}', "
        f"pick the most relevant URL and scrape it for deeper content.\n\n"
        f"Search Results:\n{state['search_result']}")[:1000]]
    })
    state["scraped_content"] = reader_result["messages"][-1].content
    
    print("\n scraped content: \n", state["scraped_content"])

    # step 4 writer chain.
    print("\n" + "="*50)
    print("writer is drafting a report...")
    print("\n" + "="*50)
    
    research_combined = (
        f"SEARCH RESULTS : \n {state['search_result']}\n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )
    
    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })
    
    print("\n final report \n", state["report"])
    
    # Critic report
    print("\n" + "="*50)
    print("critic is evaluating the report...")
    print("\n" + "="*50)
    
    state["feedback"] = critic_chain.invoke({
        "report": state["report"]
    })
    print("\n critic's evaluation \n", state["feedback"])
    
    return state

if __name__ == "__main__":
    topic = input("Enter a research topic: ")
    research_pipline(topic)