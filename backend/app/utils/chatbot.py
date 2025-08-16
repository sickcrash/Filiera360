from langchain_community.llms.ollama import Ollama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
import prompts_variables_storage

llm = Ollama(model="llama3:latest") #oppure: model="llama3.1"
chat_history = []
start = prompts_variables_storage.smaller_initprompt
productinfo= "No information available for this product at the moment"

def init_variables(productinfo):
    prompt_template_msg="{start} This is your knowledge base: {product_details}"
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                prompt_template_msg,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
    chain = prompt_template | llm
    return chain

def chatbot_response(user_prompt, itemcode, productinfo):
    question = "You: "+ user_prompt

    if question == "done":
        return "Bye bye"

    response = llm.invoke(question)
    chain=init_variables(productinfo)
    response = chain.invoke({"input": question, "chat_history": chat_history,"start":start,"product_details":productinfo})
    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=response))
    print(chat_history)
    return response