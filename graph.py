from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Interrupt,Command

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


def writer_node(state:BlogState):
    pass

def editor_node(state:BlogState):
    pass

