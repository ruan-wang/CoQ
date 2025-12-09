# streamlit run CoQ.py
import streamlit as st
import requests
import json
import re

# ========= 全局固定配置（不在界面展示） =========
OPENROUTER_API_KEY = "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"          # ← 换成你的真实 OpenRouter API Key
MODEL_NAME = "openai/gpt-4o"                        # ← 固定使用的模型
SITE_URL = "https://your-actual-site.com"           # ← 你的站点 URL，可随便填一个合法网址
SITE_NAME = "Your Site Name"                        # ← 显示在 OpenRouter 排行里的站点名

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

    # ✅ 不再展示 API Key / 模型 / 站点配置，只保留真正给用户用的输入
    subject = st.text_input(
        "请输入学科",
        value="例如：高中语文",
        help="例如：高中数学、大学计算机科学、初中物理"
    )
    core_knowledge = st.text_input(
        "请描述您想要生成的问题",
        value="例如：请生成高中课文《荷塘月色》的相关课程问题",
        help="例如：一元二次方程求解、光合作用原理"
    )

    generate_button = st.button("生成问题链", type="primary")

# --- 流式响应函数（适配 OpenRouter API） ---
def stream_response(api_key, model_name, site_url, site_name, user_prompt, placeholder):
    """
    流式获取 OpenRouter API 响应，并实时更新 Streamlit 界面。
    """
    if not api_key:
        st.error("请先在代码中配置你的 OpenRouter API Key。")
        return None

    # OpenRouter API 地址
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # 构造请求头
    headers = {
        'Authorization': f"Bearer {api_key}",
        'Content-Type': "application/json",
        'HTTP-Referer': site_url,  # 可选但建议填写
        'X-Title': site_name       # 可选但建议填写
    }
    
    # 构造请求体
    body = {
        "model": model_name,
        "messages": [{"role": "user", "content": user_prompt}],
        "stream": True,      # 开启流式传输
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0
    }
    
    full_response = ""
    
    try:
        response = requests.post(
            url=url,
            json=body,
            headers=headers,
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        
        # 解析流式响应
        for chunk in response.iter_lines():
            if chunk:
                chunk_str = chunk.decode('utf-8')
                if chunk_str.startswith('data: '):
                    chunk_str = chunk_str[6:].strip()
                    
                    if chunk_str == '[DONE]':
                        break
                    
                    try:
                        chunk_data = json.loads(chunk_str)
                        delta_content = chunk_data['choices'][0]['delta'].get('content', '')
                        if delta_content:
                            full_response += delta_content
                            placeholder.markdown(full_response)
                    except json.JSONDecodeError:
                        continue
                    except KeyError as e:
                        st.warning(f"响应格式异常，缺少字段：{e}")
                        continue
    
    except requests.exceptions.Timeout:
        st.error("请求超时，请检查网络或稍后重试")
        placeholder.markdown("**请求超时，请检查网络或稍后重试**")
    except requests.exceptions.ConnectionError:
        st.error("网络连接失败，请检查网络设置")
        placeholder.markdown("**网络连接失败，请检查网络设置**")
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP请求失败：{e}"
        st.error(error_msg)
        placeholder.markdown(f"**{error_msg}**")
        try:
            error_detail = response.json()
            st.error(f"错误详情：{error_detail}")
        except:
            pass
    except Exception as e:
        error_msg = f"未知错误：{e}"
        st.error(error_msg)
        placeholder.markdown(f"**{error_msg}**")
    
    return full_response

# --- 主界面内容渲染 ---
if generate_button:
    # 验证输入
    if not subject or not core_knowledge:
        st.warning("学科和核心知识点均为必填项。")
    elif not OPENROUTER_API_KEY:
        st.warning("请在代码顶部配置 OPENROUTER_API_KEY。")
    else:
        # 定义问题生成 Prompt
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
        final_prompt = prompt_template.format(subject=subject, core_knowledge=core_knowledge)
        
        # 清空之前的会话状态
        for key in ['raw_response', 'answers_response']:
            if key in st.session_state:
                del st.session_state[key]
        
        st.success("开始生成问题...")
        
        response_placeholder = st.empty()
        response_placeholder.markdown("正在等待大模型响应...")
        
        # 使用固定配置调用
        raw_response = stream_response(
            api_key=OPENROUTER_API_KEY,
            model_name=MODEL_NAME,
            site_url=SITE_URL,
            site_name=SITE_NAME,
            user_prompt=final_prompt,
            placeholder=response_placeholder
        )
        
        if raw_response:
            st.session_state['raw_response'] = raw_response
            st.success("问题生成完毕！")
            
            # 解析并展示关联逻辑说明
            try:
                if "关联逻辑说明：" in raw_response:
                    parts = re.split(r'关联逻辑说明：', raw_response, maxsplit=1)
                    logic_part = "关联逻辑说明：" + parts[1]
                    with st.expander("查看关联逻辑说明"):
                        st.markdown(logic_part)
                else:
                    st.info("未在生成结果中找到明确的“关联逻辑说明”部分。")
            except Exception as e:
                st.warning(f"解析关联逻辑说明时出错: {e}")
            
            st.markdown("---")
            generate_answer = st.button("生成答案", type="secondary")
            
            if generate_answer:
                answer_prompt = f"""请针对以下生成的问题链，逐一提供详细、准确的答案：

{raw_response}

### 答案输出要求：
1. 按照问题顺序逐一回答，每个答案前标注对应的问题编号
2. 答案要准确、详细，符合学科规范
3. 对于需要计算或推导的问题，展示完整的解题过程
4. 保持答案的专业性和教育性
"""
                st.success("开始生成答案...")
                answer_placeholder = st.empty()
                answer_placeholder.markdown("正在生成答案中...")
                
                answers_response = stream_response(
                    api_key=OPENROUTER_API_KEY,
                    model_name=MODEL_NAME,
                    site_url=SITE_URL,
                    site_name=SITE_NAME,
                    user_prompt=answer_prompt,
                    placeholder=answer_placeholder
                )
                
                if answers_response:
                    st.session_state['answers_response'] = answers_response
                    st.success("答案生成完毕！")

# 显示已生成的问题（未生成答案时）
elif 'raw_response' in st.session_state and 'answers_response' not in st.session_state:
    st.markdown(st.session_state['raw_response'])
    
    try:
        if "关联逻辑说明：" in st.session_state['raw_response']:
            parts = re.split(r'关联逻辑说明：', st.session_state['raw_response'], maxsplit=1)
            logic_part = "关联逻辑说明：" + parts[1]
            with st.expander("查看关联逻辑说明"):
                st.markdown(logic_part)
    except:
        pass
    
    st.markdown("---")
    generate_answer = st.button("生成答案", type="secondary")
    
    if generate_answer:
        answer_prompt = f"""请针对以下生成的问题链，逐一提供详细、准确的答案：

{st.session_state['raw_response']}

### 答案输出要求：
1. 按照问题顺序逐一回答，每个答案前标注对应的问题编号
2. 答案要准确、详细，符合学科规范
3. 对于需要计算或推导的问题，展示完整的解题过程
4. 保持答案的专业性和教育性
"""
        st.success("开始生成答案...")
        answer_placeholder = st.empty()
        answer_placeholder.markdown("正在生成答案中...")
        
        answers_response = stream_response(
            api_key=OPENROUTER_API_KEY,
            model_name=MODEL_NAME,
            site_url=SITE_URL,
            site_name=SITE_NAME,
            user_prompt=answer_prompt,
            placeholder=answer_placeholder
        )
        
        if answers_response:
            st.session_state['answers_response'] = answers_response
            st.success("答案生成完毕！")

# 显示已生成的答案
if 'answers_response' in st.session_state:
    st.markdown("---")
    st.subheader("📝 问题答案")
    st.markdown(st.session_state['answers_response'])

# --- 页脚 ---
st.markdown("---")
st.markdown("""
提示：  
1. 使用的是 OpenRouter API，请确保你的 API Key 有足够的额度（在代码中已固定配置）。  
2. 流式传输过程中，请耐心等待，不要刷新页面。  
3. 有任何问题可以邮箱联系我本人进行反馈（wangruan@mail.bnu.edu.cn）。
""")
