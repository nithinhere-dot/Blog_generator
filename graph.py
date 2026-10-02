from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt,Command
from typing import Literal
from state import BlogState
from agents import researcher_agent,writer_agent,editor_agent,get_llm

MAX_REVISIONS=3

def researcher_node(state:BlogState):
    """Researcher Node generates (or revises) the research outline"""
    llm=get_llm()
    researcher_data=researcher_agent(
        llm=llm,
        topic=state.topic,
        audience=state.audience,
        feedback=state.research_feedback
    )
    print("Researcher Output:")
    state.research=researcher_data
    state.research_feedback=""
    return state

def human_review_research_node(state:BlogState):
    """"Pause and ask the human to approve the research or send the feedback"""
    decision=interrupt({
        "stage":"researcher_review",
        "research":state.research,
        "instructions":(
            "Reply with 'approve' to approve the research outline or provide feedback for revision."
        )
    })
    if isinstance(decision,dict):##if the user said nothing, we will assume they approved the research
        action=decision.get("action","approve")
        feedback=decision.get("feedback","")
    else:
        text=str(decision)
        action="approve" if text.lower()=="approve" else "revise"
        feedback="" if action == "approve" else text
    state.research_feedback=feedback
    print("Human Review Research Output:")
    return state

def writer_node(state:BlogState):
    """writer Node generates (or revises) the full draft of the blog post"""
    llm=get_llm()
    writer_data=writer_agent(
        llm=llm,
        topic=state.topic,
        audience=state.audience,
        feedback=state.draft_feedback,
        research=state.research
    )
    state.draft=writer_data
    state.draft_feedback=""
    print("Writer Output:")
    return state

def human_review_draft_node(state:BlogState):
    """"Pause and ask the human to approve the draft or send the feedback"""
    decision=interrupt({
        "stage":"draft_review",
        "draft":state.draft,
        "instructions":(
            "Reply with 'approve' to approve the draft or provide feedback for revision."
        )
    })
    if isinstance(decision,dict):##if the user said nothing, we will assume they approved the research
        action=decision.get("action","approve")
        feedback=decision.get("feedback","")
    else:
        text=str(decision)
        action="approve" if text.lower()=="approve" else "revise"
        feedback="" if action == "approve" else text
    state.draft_feedback=feedback
    print("Human Review Draft Output:")
    return state


def editor_node(state:BlogState):
    """Editor Node generates (or revises) the final edited version of the blog post"""
    llm=get_llm()
    final=editor_agent(
        llm=llm,
        topic=state.topic,
        draft=state.draft,
    )
    state.final_blog=final 
    print("Editor Output:")
    return state


def route_after_research_review(state:BlogState)->Literal["researcher,writer"]:
    if state.research_feedback:
        return "researcher"
    else:
        return "writer"

def route_after_draft_review(state:BlogState)->Literal["writer","editor"]:
    if state.draft_feedback and state.revision_count<MAX_REVISIONS:
        return "writer"
    else:
        return "editor"


##Build and compile the graph
def build_blog_graph():
    builder=StateGraph(BlogState)

    ###add nodes
    builder.add_node("researcher",researcher_node)
    builder.add_node("human_review_research",human_review_research_node)
    builder.add_node("writer",writer_node)
    builder.add_node("human_review_draft",human_review_draft_node)
    builder.add_node("editor",editor_node)

    ###add edges
    builder.add_edge(START,"researcher")
    builder.add_edge("researcher","human_review_research")
    builder.add_edge("writer","human_review_draft")
    builder.add_edge("editor",END)


    ###add conditional edges
    builder.add_conditional_edges("human_review_research",route_after_research_review,{"researcher":"researcher","writer":"writer"})
    builder.add_conditional_edges("human_review_draft",route_after_draft_review,{"writer":"writer","editor":"editor"})

    graph=builder.compile(checkpointer=InMemorySaver())
    return graph