import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

#生成会话标识函数
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

#保存会话信息函数
def save_session():
    if st.session_state.current_session:
        session_data = {

            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)


#加载所有会话列表信息
def load_sessions():
    session_list=[]
    if os.path.exists("sessions"):
        file_list=os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list


#加载指定会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state = session_data["messages"]
                st.session_state = session_data["nick_name"]
                st.session_state = session["nature"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error("加载会话失败！")

def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name==st.session_state.current_session:
                st.session_state.messages=[]
                st.session_state.current_session=generate_session_name()

    except Exception as e:
        st.error("删除会话失败！")




st.title("AI智能伴侣")

system_prompt="""
你叫%s,你是用户的真实伴侣，请完全代入伴侣角色。
规则：
    1.匹配用户的语言
    2.回复简短，就像微信聊天一样
    3.允许使用emoji表情
    4.回复的内容，要充分体现伴侣的性格特征
伴侣性格：
    - %s
务必严格遵上述规则

"""

#初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages=[]
    #
if "nick_name" not in st.session_state:
    st.session_state.nick_name="x"
    #
if "nature" not in st.session_state:
    st.session_state.nature="开朗"

#会话标识
if "current_session" not in st.session_state:

    st.session_state.current_session=generate_session_name()




#展示聊天信息
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:

    st.chat_message(message["role"]).write(message["content"])


client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

#侧边栏
with st.sidebar:
    #会话信息
    st.subheader("AI控制面板")
    #新建会话
    if st.button("新建会话",width="stretch",icon="🔄"):

        # 保存当前会话信息
        save_session()

        #创建新的会话
        if st.session_state.messages:  #if语句，避免重复新建空的会话
            st.session_state.messages=[]
            st.session_state.current_session=generate_session_name()
            save_session()
            st.rerun()  #重新运行当前页面

    #会话历史
    st.text("会话历史")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1])  #columns-将一行分为多列，参数1为几等分
        with col1:
            #加载会话信息
            if st.button(session,width="stretch",icon="💾",key=f"load_{session}",type="primary" if session==st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()

        with col2:
            if st.button("",width="stretch",icon="❌️",key=f"delete_{session}"):
                delete_session(session)
                st.rerun()



    #分割线
    st.divider()





    #伴侣信息
    st.subheader("伴侣信息")
    #昵称输入栏
    nick_name=st.text_input("昵称",placeholder="请输入昵称：",value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name=nick_name

    nature=st.text_area("性格",placeholder="请输入性格：",value=st.session_state.nature)
    if nature:
        st.session_state.nature=nature

#消息输入框
prompt=st.chat_input("输入你的问题")
if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name,st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}

    )
    #非流式输出
    #st.chat_message("assistant").write(response.choices[0].message.content)

    response_message=st.empty()

    full_response=""
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            content=chunk.choices[0].delta.content
            full_response+=content
            response_message.chat_message("assistant").write(full_response)

    #保存大模型返回的结果
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_session()
