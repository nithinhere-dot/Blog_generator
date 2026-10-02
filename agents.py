import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

##Get LLM
def get_llm(model_name:str="gemini-3.5-flash-lite",temperature:float=0.5,):
    api_key=os.getenv("GOOGLE_API_KEY")
    llm=ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key
    )
    return llm

##Researcher Agent
RESEARCHER_PROMPT=ChatPromptTemplate.from_messages([
    {"role":"system","content":"""
        "You are a Research Agent.Given a blog topic and target audience,produce a clear"
        "structured research outline.Include:\n"
        "1.5-7 key points the blog should cover\n"
        "2.Important facts,stats,or examples for each point\n"
        "3.suggested angle or hook\n"
        "Be concise .Use bullet points.Do NOT write the full blog yet."

"""},{"role":"user","content":"Topic:{topic}\nAudience:{audience}.,{revison_hints},write the research outline now."}    
])

def researcher_agent(llm:ChatGoogleGenerativeAI,topic:str,audience:str,feedback:str=""):
    if not feedback:
        revison_hints="This is your first attempt."
    revison_hints=f"The Human provided this feedback on your previous research-please address it:{feedback}"

    chain=RESEARCHER_PROMPT | llm
    result=chain.invoke({"topic":topic,"audience":audience,"revison_hints":revison_hints})
    return result.content[0]["text"]

##writer Agent
WRITER_PROMPT=ChatPromptTemplate.from_messages([
    {"role":"system","content":"""
        "You are a Writer Agent.Given a research notes provided,write a complete"
        "engaging blog post.\n"
        "Rules:\n"
        "1.Length: 500-700 words\n"
        "2.structure:catchy title,intro hook 3-5 sections with H2 headings,conclusions\n"
        "3.Tone:clear,frienldy,suited to the target audience\n"
        "4.Use markdown formatting\n"
        "Do not add a 'word count' section at the end of the blog post.\n"

"""},
{"role":"user","content":"""
        topic:{topic},
        Research Notes:{research},
        Audience:{audience},
        {revision_hints}
    """}    
])


def writer_agent(llm:ChatGoogleGenerativeAI,topic:str,audience:str,feedback:str="",research:str=""):
    if not feedback:
        revison_hints="This is your first attempt."
    revison_hints=f"The Human provided this feedback on your previous draft and asked for these changes:{feedback},please apply these changes during writing the blog"

    chain=WRITER_PROMPT | llm
    result=chain.invoke({
        "topic":topic,
        "audience":audience,
        "revison_hints":revison_hints,
        "research":research})
    return result.content[0]["text"]


EDITOR_PROMPT=ChatPromptTemplate.from_messages([
    {"role":"system","content":"""
        "You are a Editor Agent-the final quality gate before publishing\n"
        "Take the draft and produce the FINAL polished version. Specifically:\n"
        "-Fix grammer,spelling, and awkward phrasing\n"
        "-Tighten the writing and improve clarity\n"
        "-Improve the flow and structure of the blog\n"
        "-Make the title and intros more compelling\n"
        "-Keep the same strcuture and markdown formatting\n"
        "- Blog wordings should look like human,not a AI,and don't use any special chars and complex /fancy words.\n"
        "Output only the final blog post-No commentry"

"""},
{"role":"user","content":"""
        topic:{topic},
        Draft:{draft}
        
        Return the published blog post
    """}    
])

def editor_agent(llm:ChatGoogleGenerativeAI,topic:str,draft:str):

    chain=EDITOR_PROMPT | llm
    result=chain.invoke({
        "topic":topic,
       "draft":draft
       })
    
    return result.content[0]["text"]