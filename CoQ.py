#streamlit run CoQ.py
import streamlit as st
import requests
import json
import re

# --- 页面配置 ---
st.set_page_config(page_title="链式问题生成器", page_icon="🔗", layout="wide")

# --- 应用标题和说明 ---
st.title("🔗 通用学科问题链生成")
st.markdown("""
根据指定的学科和核心知识点，生成一组具有强关联性、梯度递进的链式问题。
问题将以流式方式实时显示。请在左侧输入你的配置信息。
""")

# --- 侧边栏：用户输入 ---
with st.sidebar:
    st.header("用户配置区")
    
    # API Key 输入
    api_key = "Bearer VNDJAZymrZAarHDfQYjA:ggTmZzqeYqtMgiKuYMdq"
    
    # 学科和知识点输入
    subject = st.text_input("请输入学科", value="例如：高中语文", help="例如：高中数学、大学计算机科学、初中物理")
    core_knowledge = st.text_input("请描述您想要生成的问题", value="荷塘月色", help="例如：一元二次方程求解、光合作用原理")
    
    # 生成按钮
    generate_button = st.button("生成问题链", type="primary")

# --- 主逻辑 ---
def stream_answer(api_key, user_prompt, placeholder):
    """
    流式获取 API 响应，并实时更新 Streamlit 界面。
    """
    if not api_key:
        st.error("请先输入你的 API Key。")
        return None

    url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
    headers = {
        'Authorization': api_key,
        'Content-Type': "application/json"
    }
    
    messages = [
        {"role": "user", "content": user_prompt}
    ]
    
    body = {
        "model": "4.0Ultra",
        "messages": messages,
        "stream": True,  # 开启流式传输
        "tools": [
            {
                "type": "web_search",
                "web_search": {
                    "enable": False,
                    "search_mode": "deep"
                }
            }
        ]
    }
    
    full_response = ""
    
    try:
        response = requests.post(url=url, json=body, headers=headers, stream=True, timeout=120)
        response.raise_for_status()
        
        for chunk in response.iter_lines():
            if chunk:
                # 讯飞流式返回的数据格式为: b'data: {"id":"...", ...}'
                # 需要先去除前缀 'data: '，再进行 JSON 解析
                chunk_str = chunk.decode('utf-8')
                if chunk_str.startswith('data: '):
                    chunk_str = chunk_str[6:]
                if chunk_str.strip() == '[DONE]':
                    break
                
                try:
                    chunk_data = json.loads(chunk_str)
                    # 提取 delta 中的 content
                    delta_content = chunk_data['choices'][0]['delta'].get('content', '')
                    if delta_content:
                        full_response += delta_content
                        # 实时更新界面，使用 Markdown 渲染
                        placeholder.markdown(full_response)
                except json.JSONDecodeError:
                    # 如果解析失败，可能是不完整的 chunk，暂时忽略
                    continue
                except Exception as e:
                    st.warning(f"处理数据块时发生错误: {e}")
                    continue

    except requests.exceptions.RequestException as e:
        error_msg = f"请求 API 失败: {e}"
        st.error(error_msg)
        placeholder.markdown(f"**{error_msg}**")
        return None
    
    return full_response

# --- 主界面内容渲染 ---
if generate_button:
    # 验证输入
    if not subject or not core_knowledge:
        st.warning("学科和核心知识点均为必填项。")
    elif not api_key:
        st.warning("请输入 API Key。")
    else:
        # 定义 Prompt
        prompt_template = """通用学科链式问题生成Prompt

请你以【{subject}】领域的资深教师身份，基于以下核心要求，针对【{core_knowledge}】生成一组具有强关联性的链式问题。

### 核心要求

1.  **关联性逻辑**：问题链需遵循“基础认知→深度理解→应用迁移→拓展延伸→综合创新”的递进逻辑，后一个问题必须建立在前一个问题的答案基础上，形成环环相扣的逻辑链条，禁止出现孤立无关联的问题。

2.  **学科适配性**：问题需贴合指定学科的学科特点（如理科侧重公式推导、实验分析；文科侧重概念辨析、逻辑论证；语文学科侧重读写结合；艺术类侧重审美体验等），避免出现跨学科的无关导向。

3.  **难度梯度**：从基础题（考查对核心概念的基本记忆与识别）逐步过渡到中档题（考查对知识点的理解与简单应用），最终到提高题（考查知识迁移、综合运用或创新思考），梯度清晰可辨。

4.  **问题类型多样**：结合学科特点融入多种题型，如选择题、填空题、简答题、计算题、实验设计题、论述题、案例分析题等，避免单一题型的重复。

5.  **数量要求**：每组问题链包含5-8个问题，确保逻辑链条的完整性与紧凑性，不冗余不残缺。

### 输出规范

1.  先明确标注“学科：XXX”“核心知识点：XXX”；

2.  按顺序编号列出问题，每个问题后用括号标注题型与难度（基础/中档/提高）；

3.  最后附加一段“关联逻辑说明”，简要阐述每个问题与前一个问题的关联点，以及整体链条的递进逻辑。

### 示例引导（仅作逻辑参考，需结合指定学科调整）

学科：初中物理 核心知识点：凸透镜成像规律

1.  凸透镜的基本光学性质是什么？请列举2点（简答题，基础）

2.  基于凸透镜对光线的会聚作用，当物体位于凸透镜2倍焦距以外时，所成的像具有哪些特点（像的虚实、大小、正倒）？（简答题，基础）

...

关联逻辑说明：问题1搭建基础认知，问题2基于基础性质聚焦特定成像场景...
"""
        # 填充 Prompt
        final_prompt = prompt_template.format(subject=subject, core_knowledge=core_knowledge)
        
        # 清空之前的会话状态
        if 'raw_response' in st.session_state:
            del st.session_state['raw_response']
        
        st.success("开始生成问题...")
        
        # 创建一个占位符，用于实时更新内容
        response_placeholder = st.empty()
        # 初始显示loading信息
        response_placeholder.markdown("正在等待大模型响应...")
        
        # 调用流式函数，这会阻塞直到流传输完成
        raw_response = stream_answer(api_key, final_prompt, response_placeholder)
        
        # 流传输完成后，将完整响应存入 session_state
        if raw_response:
            st.session_state['raw_response'] = raw_response
            st.success("问题生成完毕！")
            
            # 尝试解析并展示关联逻辑说明
            try:
                if "关联逻辑说明：" in raw_response:
                    # 使用正则表达式分割，确保只分割一次
                    parts = re.split(r'关联逻辑说明：', raw_response, maxsplit=1)
                    questions_part = parts[0]
                    logic_part = "关联逻辑说明：" + parts[1]
                    
                    # 在原始位置下方展示折叠的逻辑说明
                    with st.expander("查看关联逻辑说明"):
                        st.markdown(logic_part)
                else:
                    st.info("未在生成结果中找到明确的“关联逻辑说明”部分。")
            except Exception as e:
                st.warning(f"解析关联逻辑说明时发生错误: {e}")

# --- 调试区域 ---
with st.expander("调试：查看原始 API 响应", expanded=False):
    if 'raw_response' in st.session_state:
        st.text_area("完整的原始响应", value=st.session_state['raw_response'], height=300)
    else:
        st.info("请先生成问题以查看原始响应。")

# --- 页脚 ---
st.markdown("---")
st.markdown("""
    提示：
    1.  本网站最多同时在线人数为5人（个人项目，请理解）。
    2.  流式传输过程中，请耐心等待，不要刷新页面。
    3.  有任何问题可以邮箱联系我本人进行反馈（wangruan@mail.bnu.edu.cn）。
""")