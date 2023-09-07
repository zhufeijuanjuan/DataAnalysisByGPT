"""
@Time   : 2023/8/11 16:57
@Author : figo_zhu
@File   : langchain_analyzer.py
@Desc   : use llm model to do data analysis
"""
import os
import streamlit as st
from streamlit_chat import message
import pandas as pd
from langchain.schema import HumanMessage
from langchain.chat_models import AzureChatOpenAI

os.environ['OPENAI_API_KEY'] = '10db07ece95844898f99349b530ca032'

class Interpreter:
    """
    将自然语言转成代码并执行，返回执行结果
    """
    def __init__(self):
        """ChatGPT初始化"""
        self.llm = AzureChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_type="azure",
            openai_api_base="https://openai-testdev-trial.openai.azure.com/",
            openai_api_version="2023-07-01-preview",
            deployment_name="Test-chatGPT",
            temperature=0.7,
            max_tokens=800
        )
    def __getattr__(self, function_name):
        def method(*args, **kwargs):
            generated_code = self._run_llm(function_name, *args, **kwargs)
            print(f'-----------------------generated_code-----------------------')
            print(generated_code)
            try:
                exec(generated_code, globals())
                result = eval(f"{function_name}(*args, **kwargs)")
                print(f'result: {result}\n')
                return result
            except Exception as e:
                print(f"Error when execute code: {e}")
                return None
        return method

    def _run_llm(self, query, *args, **kwargs):
        prompt = f"""
        please help me to write a python function to achieve requirements in the input query. you should strickly comply
        the following rules:
        - the function name must be <{query}>;
        - all needed package should be imported under the function;
        - input parameters example is given as: *{args}, every parameter must be given a default value: None;
        - if the purpose of input query is data check, calculation or other analysis, the generated code must return the final execute result;
        - if the purpose of input query is plot figures, the generated code must save the figure with filename: {query}.jpg in current path and put the saved filename as return;
        - don't use any 'pass' operation;
        - you only need to output the code you generated, not any explain or test needed.
        """
        try:
            response = self.llm([HumanMessage(content=prompt)])
            # TODO: use agent and tools function in langchain to support multiple tasks, such as data analysis, chat, etc.
            response = response.content
            response = response.replace('```python', '').replace('```', '').strip()
            return response

        except Exception as e:
            print(f"Error when run llm to generate code: {e}")
            return None

@st.cache_data
def load_data(file):
    file_extension = file.name.split(".")[-1]
    if file_extension == "csv":
        df = pd.read_csv(file, encoding="utf-8")
    elif file_extension == "xlsx":
        df = pd.read_excel(file, engine="openpyxl")
    else:
        df = None
    return df

def main():
    code_interperter = Interpreter()

    st.title("Data Analysis based on ChatGPT")
    # Upload CSV or Excel data
    data = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

    if data is not None:
        df = load_data(data)
        if df is not None:
            df
            st.success("File uploded successfully!")
        else:
            st.error("File uploded failed!")

        if 'history' not in st.session_state:
            st.session_state['history'] = []
        if 'generated' not in st.session_state:
            st.session_state['generated'] = []
        if 'past' not in st.session_state:
            st.session_state['past'] = []

        response_container = st.container()
        container = st.container()

        with container:
            with st.form(key='my_form', clear_on_submit=True):
                query = st.text_input("user", placeholder="enter your query here", key='input')
                submit_button = st.form_submit_button(label='submit')
            if submit_button and query:
                query_ = "_".join(query.split())
                response = code_interperter.__getattr__(query_).__call__(df)
                print("response:", response)
                st.session_state['past'].append(query)
                st.session_state['generated'].append(str(response))

        if st.session_state['generated']:
            with response_container:
                for i in range(len(st.session_state['generated'])):
                    message(st.session_state['past'][i], is_user=True, key=str(i)+'_user', avatar_style='big-smile',)
                    message(st.session_state['generated'][i], is_user=True, key=str(i), avatar_style='thumb')
                if str(response).endswith(".jpg"):
                    try:
                        st.image(response)
                    except:
                        st.error("figure not exist!")
    else:
        st.warning("Please upload a CSV or Excel file first.")


if __name__ == "__main__":
    main()
