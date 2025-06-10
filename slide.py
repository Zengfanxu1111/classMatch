import gradio as gr
import numpy as np
import json # 导入json库用于数据序列化

# 1. 初始化色块（业务）的位置和属性
initial_blocks = {
    "业务A (5G)": {"rect": [0.1, 0.1, 0.2, 0.2], "facecolor": "skyblue"},
    "业务B (Wi-Fi)": {"rect": [0.4, 0.1, 0.2, 0.2], "facecolor": "lightgreen"},
    "业务C (卫星)": {"rect": [0.7, 0.1, 0.2, 0.2], "facecolor": "salmon"},
}

def generate_spectrum_html(blocks_state, selected_key_name, json_input_comp_id):
    """
    生成包含 SVG 图形和 JavaScript 交互逻辑的 HTML 字符串。
    Args:
        blocks_state (dict): 当前所有色块的状态。
        selected_key_name (str): 当前选中的色块的键名，用于高亮。
        json_input_comp_id (str): 隐藏的 gr.JSON 输入组件的元素 ID，用于 JS 回传数据。
    Returns:
        str: 完整的 HTML 字符串。
    """
    svg_elements = []

    # 绘制总带宽条
    svg_elements.append(f"""
        <rect x="0.05" y="0.8" width="0.9" height="0.1" fill="whitesmoke" stroke="black" stroke-width="0.002"></rect>
        <text x="0.5" y="0.85" text-anchor="middle" dominant-baseline="middle" font-size="0.03" fill="black">总可用带宽</text>
    """)

    # 绘制色块
    for key, properties in blocks_state.items():
        x, y, w, h = properties["rect"]
        facecolor = properties["facecolor"]
        edge_color = 'red' if key == selected_key_name else 'black'
        line_width = 0.003 if key == selected_key_name else 0.001 # 在0-1 viewBox中，线宽也要归一化

        svg_elements.append(f"""
            <rect id="block-{key}" x="{x}" y="{y}" width="{w}" height="{h}"
                  fill="{facecolor}" stroke="{edge_color}" stroke-width="{line_width}"
                  data-key="{key}" style="cursor: grab;"></rect>
            <text x="{x + w/2}" y="{y + h/2}" text-anchor="middle" dominant-baseline="middle"
                  font-size="0.04" fill="black" pointer-events="none">{key}</text>
        """)

    # 将 Python 的 blocks_state 和 selected_key_name 转换为 JSON 字符串，供 JS 初始化
    blocks_json_str = json.dumps(blocks_state)
    selected_key_json_str = json.dumps(selected_key_name)

    # JavaScript 交互逻辑
    js_code = f"""
    <script type="text/javascript">
        // 确保 Gradio 库已加载
        if (typeof Gradio === 'undefined' || !Gradio.mountGradioApp) {{
            console.warn('Gradio JavaScript not loaded. Skipping interactive setup.');
            // Fallback for when script is loaded before Gradio core
            document.addEventListener('DOMContentLoaded', function() {{
                if (typeof Gradio !== 'undefined' && Gradio.mountGradioApp) {{
                    setupInteractiveSVG();
                }}
            }});
        }} else {{
            setupInteractiveSVG();
        }}

        function setupInteractiveSVG() {{
            const svg = document.getElementById('spectrum-svg');
            if (!svg) {{
                console.error('SVG element not found.');
                return;
            }}

            let blocksState = {blocks_json_str}; // 初始化前端状态
            let selectedKey = {selected_key_json_str}; // 初始化选中状态
            let currentDragElement = null;
            let offset = {{x: 0, y: 0}}; // 鼠标点击位置与元素左上角的偏移

            // 获取Gradio的隐藏输入组件，用于将数据回传给Python
            const gradioJsonInput = document.getElementById('{json_input_comp_id}');
            // 确保 Gradio 的 update 方法可用，这是 Gradio 3.x+ 的推荐方式
            // 或者使用 Gradio.dispatch(...) for older versions if needed
            // const sendDataToGradio = (data) => {{
            //     if (gradioJsonInput && gradioJsonInput._update_value) {{
            //         // This is a private method, but often used for direct JS updates
            //         gradioJsonInput._update_value(JSON.stringify(data));
            //     }} else if (window.gradio.dispatch) {{ // Fallback for older Gradio versions
            //         window.gradio.dispatch('{json_input_comp_id}', 'change', JSON.stringify(data));
            //     }}
            // }};
            // For Gradio 4.x and newer, direct element property setting often works:
            const sendDataToGradio = (data) => {{
                if (gradioJsonInput) {{
                    gradioJsonInput.value = JSON.stringify(data);
                    // Manually dispatch change event if Gradio doesn't auto-detect
                    const event = new Event('change');
                    gradioJsonInput.dispatchEvent(event);
                }}
            }};


            // 将像素坐标转换为 SVG 的 viewBox 坐标 (0-1)
            function getSvgPoint(evt) {{
                const pt = svg.createSVGPoint();
                pt.x = evt.clientX;
                pt.y = evt.clientY;
                const ctm = svg.getScreenCTM().inverse();
                return pt.matrixTransform(ctm);
            }}

            function drawBlocks() {{
                // This function is only for initial rendering or when the state is updated from Python
                // For drag and drop, we modify existing elements directly.
                // Re-rendering the whole SVG is handled by Python regenerating the HTML.
            }}

            svg.addEventListener('mousedown', function(evt) {{
                evt.preventDefault(); // 阻止默认的拖拽行为，如图片拖拽
                const target = evt.target;
                const key = target.getAttribute('data-key');

                if (key) {{ // 点击到色块
                    if (selectedKey === key) {{
                        // 再次点击已选中的块，准备拖拽
                        currentDragElement = target;
                        const svgPoint = getSvgPoint(evt);
                        // 计算鼠标点击位置与色块左上角的偏移
                        offset.x = svgPoint.x - parseFloat(target.getAttribute('x'));
                        offset.y = svgPoint.y - parseFloat(target.getAttribute('y'));
                        target.style.cursor = 'grabbing';
                    }} else {{
                        // 选中新块，或取消选中旧块并选中新块
                        selectedKey = key;
                        // 重新绘制，让 Python 后端来处理高亮
                        sendDataToGradio({{ blocks: blocksState, selected_key: selectedKey }});
                    }}
                }} else {{ // 点击到空白区域
                    if (currentDragElement) {{
                        // 如果正在拖拽一个块，则放置它
                        const draggedKey = currentDragElement.getAttribute('data-key');
                        const x = parseFloat(currentDragElement.getAttribute('x'));
                        const y = parseFloat(currentDragElement.getAttribute('y'));
                        const w = parseFloat(currentDragElement.getAttribute('width'));
                        const h = parseFloat(currentDragElement.getAttribute('height'));

                        blocksState[draggedKey].rect = [x, y, w, h];
                        currentDragElement = null;
                        selectedKey = null; // 放置后取消选中
                        target.style.cursor = 'default';
                        sendDataToGradio({{ blocks: blocksState, selected_key: selectedKey }});

                    }} else if (selectedKey) {{
                        // 如果有选中的块但点击了空白区域，并且不是拖拽，则放置它到点击位置
                        // (这与你的原始逻辑一致：选中后点击空白处放置)
                        const blockToMove = blocksState[selectedKey];
                        const svgPoint = getSvgPoint(evt);

                        let new_x = svgPoint.x - blockToMove.rect[2] / 2;
                        let new_y = svgPoint.y - blockToMove.rect[3] / 2;

                        // 边界检查 (0-1 范围)
                        new_x = Math.max(0.0, Math.min(1.0 - blockToMove.rect[2], new_x));
                        new_y = Math.max(0.0, Math.min(1.0 - blockToMove.rect[3], new_y));

                        blocksState[selectedKey].rect = [new_x, new_y, blockToMove.rect[2], blockToMove.rect[3]];
                        selectedKey = null; // 放置后取消选中
                        sendDataToGradio({{ blocks: blocksState, selected_key: selectedKey }});

                    }} else {{
                        // 什么都没选中，点击了空白处
                        selectedKey = null;
                        sendDataToGradio({{ blocks: blocksState, selected_key: selectedKey }});
                    }}
                }}
            }});

            svg.addEventListener('mousemove', function(evt) {{
                if (currentDragElement) {{
                    evt.preventDefault(); // 阻止默认的滚动等行为
                    const svgPoint = getSvgPoint(evt);
                    let new_x = svgPoint.x - offset.x;
                    let new_y = svgPoint.y - offset.y;

                    const blockWidth = parseFloat(currentDragElement.getAttribute('width'));
                    const blockHeight = parseFloat(currentDragElement.getAttribute('height'));

                    // 边界检查 (0-1 范围)
                    new_x = Math.max(0.0, Math.min(1.0 - blockWidth, new_x));
                    new_y = Math.max(0.0, Math.min(1.0 - blockHeight, new_y));

                    currentDragElement.setAttribute('x', new_x);
                    currentDragElement.setAttribute('y', new_y);

                    // 同步更新文本位置
                    const textElement = document.querySelector(`#spectrum-svg text[x='${parseFloat(currentDragElement.getAttribute('x')) + blockWidth/2}'][y='${parseFloat(currentDragElement.getAttribute('y')) + blockHeight/2}']`);
                    // Note: This text selection logic is fragile. It's better to manage text elements by ID too.
                    // For simplicity in this example, it's omitted as the whole SVG regenerates on mouseup.
                    // If you want smooth real-time text dragging, give text elements unique IDs.
                }}
            }});

            svg.addEventListener('mouseup', function(evt) {{
                if (currentDragElement) {{
                    const draggedKey = currentDragElement.getAttribute('data-key');
                    const x = parseFloat(currentDragElement.getAttribute('x'));
                    const y = parseFloat(currentDragElement.getAttribute('y'));
                    const w = parseFloat(currentDragElement.getAttribute('width'));
                    const h = parseFloat(currentDragElement.getAttribute('height'));

                    blocksState[draggedKey].rect = [x, y, w, h];
                    currentDragElement.style.cursor = 'grab';
                    currentDragElement = null;
                    selectedKey = null; // 放置后取消选中

                    sendDataToGradio({{ blocks: blocksState, selected_key: selectedKey }});
                }}
            }});
        }}
    </script>
    """

    full_html = f"""
    <div style="text-align: center;">
        <svg id="spectrum-svg" width="100%" height="400" viewBox="0 0 1 1" preserveAspectRatio="xMidYMid meet"
             style="border: 1px solid #ccc; background-color: #f9f9f9; cursor: default;">
            <title>频段分配示意图 (拖拽或点击放置)</title>
            {"".join(svg_elements)}
        </svg>
    </div>
    {js_code}
    """
    return full_html


# 后端处理函数：接收前端数据，更新状态，并触发重新渲染 HTML
def update_backend_state(frontend_data_json, current_blocks_state, current_selected_key):
    """
    这个函数接收来自前端的 JSON 数据，更新后端的 gr.State，
    并返回新的 HTML 内容和更新后的 gr.State。
    """
    try:
        frontend_data = json.loads(frontend_data_json)
        updated_blocks = frontend_data.get('blocks', current_blocks_state)
        updated_selected_key = frontend_data.get('selected_key', current_selected_key)

        # 可以在这里添加额外的业务逻辑，比如检查碰撞、保存数据等
        # 暂时直接使用前端传回的状态
        new_blocks_state = updated_blocks
        new_selected_key = updated_selected_key

        # 返回新的 HTML 和更新后的后端状态
        return (
            generate_spectrum_html(new_blocks_state, new_selected_key, "js_blocks_input_id"),
            new_blocks_state,
            new_selected_key
        )
    except Exception as e:
        print(f"Error processing frontend data: {e}")
        # 发生错误时，返回当前状态以避免 UI 崩溃
        return (
            generate_spectrum_html(current_blocks_state, current_selected_key, "js_blocks_input_id"),
            current_blocks_state,
            current_selected_key
        )


# --- Gradio 界面 ---
with gr.Blocks() as demo:
    gr.Markdown("## 频段分配小工具 (HTML/SVG/JS 版本)")
    gr.Markdown("交互方式: **点击一个色块**选中它（红色边框），**再次点击**它来拖拽；或在选中后**点击空白处**来放置。")

    # State 用于存储所有色块的位置信息
    blocks_state = gr.State(value=initial_blocks)
    # State 用于存储当前被选中的色块的key
    selected_block_key = gr.State(value=None)

    # 隐藏的 gr.JSON 组件，用于 JavaScript 向 Python 发送数据
    # elem_id 是关键，JavaScript 将通过这个 ID 找到并更新它
    js_blocks_input = gr.Json(visible=False, elem_id="js_blocks_input_id")

    # 主要的 HTML 显示区域
    spectrum_html_output = gr.HTML(
        value=generate_spectrum_html(initial_blocks, None, "js_blocks_input_id")
    )

    # 当 js_blocks_input 的值发生变化时（由前端 JS 触发），调用后端函数
    # 接收 js_blocks_input 的值，以及当前的 blocks_state 和 selected_block_key
    # 输出是新的 spectrum_html_output 内容，以及更新后的 blocks_state 和 selected_block_key
    js_blocks_input.change(
        fn=update_backend_state,
        inputs=[js_blocks_input, blocks_state, selected_block_key],
        outputs=[spectrum_html_output, blocks_state, selected_block_key]
    )

demo.launch()