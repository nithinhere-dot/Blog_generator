from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Interrupt,Command
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
    state.research=researcher_data
    state.research_feedback=""
    return state

def human_review_research_node(state:BlogState):
    """"Pause and ask the human to approve the research or send the feedback"""
    decision=Interrupt({
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
        feedback="" if action is "approve" else text
    state.research_feedback=feedback
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
    return state

def human_review_draft_node(state:BlogState):
    """"Pause and ask the human to approve the draft or send the feedback"""
    decision=Interrupt({
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
        feedback="" if action is "approve" else text
    state.draft_feedback=feedback
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
    return state


def human_review_research_node(state:BlogState)->Literal["researcher,writer"]:
    if state.research_feedback:
        return "researcher"
    else:
        return "writer"

def human_review_draft_node(state:BlogState)->Literal["writer","final"]:
    if state.draft_feedback and state.revision_count<MAX_REVISIONS:
        return "writer"
    else:
        return "final"
    