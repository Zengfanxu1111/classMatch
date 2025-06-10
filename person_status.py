import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
from matplotlib.font_manager import FontProperties
import textwrap  # For wrapping long text in nodes

# Attempt to set Chinese font
try:
    font_paths = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    zh_font = None
    for font_path in font_paths:
        fname = os.path.basename(font_path).lower()
        # Prioritize more common and robust Chinese fonts
        if 'simhei' in fname:
            zh_font = matplotlib.font_manager.FontProperties(fname=font_path)
            break
        elif 'msyh' in fname: # Microsoft YaHei
            zh_font = matplotlib.font_manager.FontProperties(fname=font_path)
            break
        elif 'wqy' in fname: # WenQuanYi series
            zh_font = matplotlib.font_manager.FontProperties(fname=font_path)
            break
        elif 'ukai' in fname or 'uming' in fname: # For Linux systems usually
            zh_font = matplotlib.font_manager.FontProperties(fname=font_path)
            break

    if zh_font:
        plt.rcParams['font.sans-serif'] = [zh_font.get_name()]
        # print(f"Using Chinese font: {zh_font.get_name()} ({font_path})") # Optional debug print
    else:
        print("Warning: Could not find common Chinese fonts. Falling back. Chinese labels might not display correctly.")
        # Added more common Chinese fonts for better fallback on Windows/Linux
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'Arial Unicode MS',
                                           'sans-serif'] # Added sans-serif fallback

    plt.rcParams['axes.unicode_minus'] = False  # Correctly display minus signs
except Exception as e:
    print(f"Error setting Chinese font in person_status.py: {e}")
    print("Chinese labels might not display correctly.")


def plot_attribute_radar(character_name, attributes, values,
                         max_value=100, color='skyblue', title=None, figsize=(8, 8)):
    """
    Generates a radar chart for a single set of attributes.

    Args:
        character_name (str): Name for the legend.
        attributes (list[str]): List of attribute names.
        values (list[float/int] or np.ndarray): List of attribute values.
        max_value (int): Max value for the radar chart axis.
        color (str): Color for the plot.
        title (str or None): Chart title.
        figsize (tuple): Figure size.

    Returns:
        tuple: (matplotlib.figure.Figure, matplotlib.axes._subplots.PolarAxesSubplot)
    """
    num_attributes = len(attributes)
    if num_attributes != len(values):
        raise ValueError(f"Attributes list length ({num_attributes}) must match values list length ({len(values)}).")
    if num_attributes < 3:
        raise ValueError("At least 3 attributes are needed to draw a polygon radar chart.")

    values = np.array(values)
    angles = np.linspace(0, 2 * np.pi, num_attributes, endpoint=False).tolist()
    plot_values = np.concatenate((values, [values[0]]))
    plot_angles = angles + angles[:1]

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    ax.plot(plot_angles, plot_values, linewidth=2, linestyle='solid', label=character_name, color=color)
    ax.fill(plot_angles, plot_values, color, alpha=0.4)

    ax.set_xticks(angles)
    ax.set_xticklabels(attributes)

    num_yticks = 5
    y_tick_step = max_value / num_yticks
    y_ticks = np.arange(0, max_value + y_tick_step, y_tick_step)

    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{int(yt)}" if yt > 0 else "" for yt in y_ticks])
    ax.set_ylim(0, max_value)
    ax.set_rlabel_position(0)

    ax.grid(True, linestyle='--', alpha=0.7)

    if title is None:
        plot_title = f'{character_name} 能力雷达图'
    else:
        plot_title = title
    ax.set_title(plot_title, size=16, y=1.08)

    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1.0), frameon=False)
    fig.tight_layout(rect=[0, 0, 0.95, 1])  # Adjust layout for legend

    return fig, ax


def plot_history_radar(student_name, submissions, max_value=100, figsize=(9, 9)):
    """
    绘制学生最近N次（最多5次）成绩的对比雷达图，显示能力成长情况。

    Args:
        student_name (str): 学生姓名。
        submissions (list): 最近提交记录列表（每个元素是 dict: {'scores': [], 'attributes': []}）。
        max_value (int): 雷达图最大值。
        figsize (tuple): 图表尺寸。

    Returns:
        tuple: (matplotlib.figure.Figure, matplotlib.axes._subplots.PolarAxesSubplot)
    """
    if not submissions:
        raise ValueError("没有提交记录可用于绘制成长雷达图。")
    if len(submissions[0]['attributes']) < 3:
        raise ValueError("至少需要3个能力维度才能绘制雷达图。")

    num_attributes = len(submissions[0]['attributes'])
    attributes = submissions[0]['attributes']  # 所有提交使用相同的属性维度

    angles = np.linspace(0, 2 * np.pi, num_attributes, endpoint=False).tolist()
    plot_angles = angles + angles[:1]  # 闭合角度

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # 使用tab10颜色映射，为每条线提供不同颜色
    try:
        from matplotlib import colormaps as cmaps
        cmap = cmaps.get_cmap('tab10')
    except (ImportError, AttributeError):
        import matplotlib.cm as cm
        cmap = cm.get_cmap('tab10')

    for i, submission in enumerate(submissions):
        scores = submission['scores']
        plot_values = np.concatenate((np.array(scores), [scores[0]]))  # 闭合数值

        # 获取颜色，确保即使只有一次提交也能获取颜色
        if len(submissions) > 1:
            color = cmap(i / (len(submissions) - 1))
        else:
            color = cmap(0.5)  # For single submission, pick a middle color

        # 绘制轨迹和填充
        ax.plot(plot_angles, plot_values,
                linewidth=2, linestyle='solid',
                label=f'第{i + 1}次提交',  # 标签显示“第X次提交”
                color=color)
        ax.fill(plot_angles, plot_values, color, alpha=0.3)

    # 设置坐标轴
    ax.set_xticks(angles)
    ax.set_xticklabels(attributes)
    ax.set_yticks(np.arange(0, max_value + 10, 10))
    ax.set_ylim(0, max_value)
    ax.set_rlabel_position(0)
    ax.grid(True, linestyle='--', alpha=0.7)

    # 设置标题和图例
    ax.set_title(f'{student_name} 最近{len(submissions)}次能力变化图', size=16, y=1.08)
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1.0), frameon=False)
    fig.tight_layout(rect=[0, 0, 0.95, 1])  # 调整图例位置

    return fig, ax


# --- Revised `plot_comparison_radar` function ---
def plot_comparison_radar(list_of_name_and_scores, attributes, max_value=100, figsize=(9, 9)):
    """
    绘制多个学生（或多次提交）的对比雷达图。

    Args:
        list_of_name_and_scores (list[tuple]): 包含 (student_name, scores_list) 的列表。
        attributes (list[str]): 共同的属性维度名称列表。
        max_value (int): 雷达图的最大值。
        figsize (tuple): 图表尺寸。

    Returns:
        tuple: (matplotlib.figure.Figure, matplotlib.axes._subplots.PolarAxesSubplot)
    """
    if not list_of_name_and_scores or len(list_of_name_and_scores) < 2:
        raise ValueError("至少需要两位学生的数据才能绘制总体能力对比图。")
    if not attributes or len(attributes) < 3:
        raise ValueError("至少需要3个能力维度才能绘制雷达图。")

    num_attributes = len(attributes)
    angles = np.linspace(0, 2 * np.pi, num_attributes, endpoint=False).tolist()
    plot_angles = angles + angles[:1] # Close the loop

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # Use tab10 colormap
    try:
        from matplotlib import colormaps as cmaps
        cmap = cmaps.get_cmap('tab10')
    except (ImportError, AttributeError):
        import matplotlib.cm as cm
        cmap = cm.get_cmap('tab10')

    # Generate colors based on number of students
    colors_list = [cmap(i / (len(list_of_name_and_scores) - 1)) if len(list_of_name_and_scores) > 1 else cmap(0.5) for i in range(len(list_of_name_and_scores))]

    for i, (student_name, scores) in enumerate(list_of_name_and_scores):
        plot_val = np.concatenate((np.array(scores), [scores[0]])) # Close the loop for values
        color = colors_list[i % len(colors_list)] # Cycle colors if more students than colors in cmap

        ax.plot(plot_angles, plot_val, linewidth=2, linestyle='solid', label=student_name, color=color)
        ax.fill(plot_angles, plot_val, color, alpha=0.3)

    # Set shared labels and ticks
    ax.set_xticks(angles)
    ax.set_xticklabels(attributes)
    num_yticks = 5
    y_tick_step = max_value / num_yticks
    y_ticks = np.arange(0, max_value + y_tick_step, y_tick_step)

    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{int(yt)}" if yt > 0 else "" for yt in y_ticks])
    ax.set_ylim(0, max_value)
    ax.set_rlabel_position(0) # Position labels

    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_title("总体能力对比", size=16, y=1.08)
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1.0), frameon=False)
    fig.tight_layout(rect=[0, 0, 0.95, 1]) # Adjust layout

    return fig, ax


# --- 新增：绘制学习路线思维导图函数 ---

# 定义错误类型到通用学习建议的映射 (更详细和全面的映射可以进一步扩展)
# Key: (section_title, error_type, specific_hint_for_detail_match)
# specific_hint_for_detail_match 可以是 col_header, field_label 或 message 中的关键词
# None 表示该类型下的通用建议
RECOMMENDATIONS_MAP = {
    # （3）信道段参数 - 信道频率规划
    ("（3）信道段参数", "dropdown", "信道类型选择"): "复习信道类型（'uu'/'aa'）的选择与意义。确保选择正确，才能进行后续频率逻辑检查。",
    ("（3）信道段参数", "dataframe_cell",
     "下行起始频率"): "检查下行起始频率是否在指定范围内（'uu'模式12.25-12.75MHz，'aa'模式19.6-21.2MHz）。",
    ("（3）信道段参数", "dataframe_cell",
     "下行终止频率"): "检查下行终止频率是否在指定范围内（'uu'模式12.25-12.75MHz，'aa'模式19.6-21.2MHz）。",
    ("（3）信道段参数", "dataframe_cell",
     "上行起始频率"): "检查上行起始频率是否在指定范围内（'uu'模式14.0-14.5MHz，'aa'模式29.4-31.0MHz）。",
    ("（3）信道段参数", "dataframe_cell",
     "上行终止频率"): "检查上行终止频率是否在指定范围内（'uu'模式14.0-14.5MHz，'aa'模式29.4-31.0MHz）。",
    ("（3）信道段参数", "logic_check_failed",
     "上行起始频率"): "检查上行起始频率是否与下行起始频率保持正确的偏移关系（'uu'模式+1.75MHz，'aa'模式+9.8MHz）。",
    ("（3）信道段参数", "logic_check_failed",
     "上行终止频率"): "检查上行终止频率是否与下行终止频率保持正确的偏移关系（'uu'模式+1.75MHz，'aa'模式+9.8MHz）。",
    ("（3）信道段参数", "frequency_logic_error", None): "信道段上行终止频率不应大于下行起始频率，请核对频率分配逻辑。", # NEW
    ("（3）信道段参数", "dataframe_format_error", None): "确保信道段参数表格格式正确，所有频率值均以数字填写，且表格结构完整。",
    ("（3）信道段参数", "data_type_error", None): "信道段频率值必须是数字，请检查输入格式。",
    ("（3）信道段参数", "column_count_mismatch", None): "信道段参数表格列数不匹配，请核对表格结构。",

    # （4）信道套参数 - 信道业务参数
    ("（4）信道套参数", "dataframe_cell", None): "复习信道套参数（TDM/ALOHA、速率、中心频点、带宽）的正确配置。",
    ("（4）信道套参数", "row_count_mismatch", None): "核对信道套参数表格行数是否完整。",
    ("（4）信道套参数", "column_count_mismatch", None): "检查信道套参数表格的列数是否正确。",
    ("（4）信道套参数", "dataframe_format_error", None): "确保信道套参数表格格式正确，数值填写无误。",

    # 1.组网参数分析 - 组网信息分析
    ("1.组网参数分析", "dataframe_duplicate", "CC地址"): "深入学习CC地址规划规范，确保每台通信控制器（CC）的地址是唯一的。",
    ("1.组网参数分析", "dataframe_format_error", None): "检查组网参数分析表格的整体格式，确保数据可被正确解析。",

    # 2.点对点通信参数 - 点对点业务参数
    ("2.点对点通信参数", "textbox", "本端CC地址"): "核对本端CC地址的正确填写格式和值。",
    ("2.点对点通信参数", "textbox", "对端XX地址"): "核对对端XX地址的正确填写格式和值。",
    ("2.点对点通信参数", "dataframe_cell", None): "复习点对点业务参数（速率、带宽、频率范围）的配置要求。",
    ("2.点对点通信参数", "frequency_logic_error", None): "点对点通信上行终止频率不应大于下行起始频率，请核对频点配置。", # NEW
    ("2.点对点通信参数", "bandwidth_rate_mismatch", None): "请根据速率（kbps）检查带宽（khz）是否满足KBP映射文件中定义的最低要求，确保带宽大于等于对应值。", # NEW
    ("2.点对点通信参数", "kbp_load_error", None): "KBP映射文件加载失败或为空，请检查kbp.txt文件是否存在和格式是否正确。", # NEW
    ("2.点对点通信参数", "row_count_mismatch", None): "核对点对点通信参数表格行数是否完整。",
    ("2.点对点通信参数", "column_count_mismatch", None): "检查点对点通信参数表格的列数是否正确。",
    ("2.点对点通信参数", "dataframe_format_error", None): "确保点对点通信参数表格格式正确。",

    # 3.虚拟子网参数 - 虚拟子网参数
    ("3.虚拟子网参数", "dataframe_cell", None): "复习虚拟子网参数（带宽、频率）的配置规范。",
    ("3.虚拟子网参数", "frequency_logic_error", None): "虚拟子网上行终止频率不应大于下行起始频率，请核对频点配置。", # NEW
    ("3.虚拟子网参数", "row_count_mismatch", None): "核对虚拟子网参数表格行数是否完整。",
    ("3.虚拟子网参数", "column_count_mismatch", None): "检查虚拟子网参数表格的列数是否正确。",
    ("3.虚拟子网参数", "dataframe_format_error", None): "确保虚拟子网参数表格格式正确。",

    # 通用格式错误建议 (当无法匹配到具体单元格时)
    (None, "格式错误或解析失败", None): "请检查该部分答卷的填写格式是否符合要求，确保数据可被系统正确解析。",
    (None, "未知错误数", None): "该部分发生未知错误，请联系教师检查。",
    (None, "data_type_error", None): "数据类型错误，请确保在数字字段输入的是数字。",
    (None, "logic_check_failed", None): "逻辑检查失败，请复习该模块的业务逻辑和参数间关系。"
}


def get_study_recommendation(detailed_error):
    """
    根据详细错误信息获取具体的学习建议。
    尝试匹配最具体的建议，如果无，则返回通用建议。
    """
    section_title = detailed_error.get('section_title')
    error_type = detailed_error.get('type')
    specific_hint = None

    if error_type == 'textbox':
        specific_hint = detailed_error.get('field_label')
    elif error_type in ['dataframe_cell', 'dataframe_duplicate']:
        specific_hint = detailed_error.get('col_header')
    elif error_type == 'dropdown':
        specific_hint = detailed_error.get('field_label')
    elif error_type == 'logic_check_failed':
        # For logic_check_failed, message might contain specific hints or target columns.
        # Example: 'user_value': '13.0', 'answer_value': 'uu 模式下应为 下行起始频率+1.75'
        # The 'answer_value' could provide a hint.
        # Let's try matching specific parts of the message.
        if "下行起始频率" in detailed_error.get('answer_value', ''):
            specific_hint = "下行起始频率"
        elif "下行终止频率" in detailed_error.get('answer_value', ''):
            specific_hint = "下行终止频率"
        elif "上行起始频率" in detailed_error.get('answer_value', ''):
            specific_hint = "上行起始频率"
        elif "上行终止频率" in detailed_error.get('answer_value', ''):
            specific_hint = "上行终止频率"
    elif error_type in ['frequency_logic_error', 'bandwidth_rate_mismatch', 'kbp_load_error']: # NEW
        # For these new types, the recommendation is generally tied to the section and type
        specific_hint = None

    # Try specific match (section, type, specific_hint)
    if (section_title, error_type, specific_hint) in RECOMMENDATIONS_MAP:
        return RECOMMENDATIONS_MAP[(section_title, error_type, specific_hint)]

    # Try general error type match for the section (section, type, None)
    if (section_title, error_type, None) in RECOMMENDATIONS_MAP:
        return RECOMMENDATIONS_MAP[(section_title, error_type, None)]

    # Try global error type match (None, type, None) for common types like format/data type
    if (None, error_type, None) in RECOMMENDATIONS_MAP:
        return RECOMMENDATIONS_MAP[(None, error_type, None)]

    # If no specific match, return a general recommendation
    return f"针对 '{section_title}' 部分的 '{error_type}' 错误，建议复习相关知识点。"


def plot_study_route_mindmap(student_name, detailed_errors, figsize=(12, 10)):
    """
    绘制学生的学习路线思维导图。

    Args:
        student_name (str): 学生姓名。
        detailed_errors (list[dict]): 详细的错误信息列表。
        figsize (tuple): 图表尺寸。

    Returns:
        tuple: (matplotlib.figure.Figure, matplotlib.axes._subplots.PolarAxesSubplot)
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("#fcfcfc")  # Lighter background for mindmap feel
    ax.set_xlim(0, 1)  # Normalized coordinates
    ax.set_ylim(0, 1)  # Initial ylim, will be adjusted later based on content
    ax.axis('off')  # Hide axes

    # Must draw canvas once to get a renderer that can measure text accurately
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    # Map section titles to more user-friendly capability names for main branches
    section_to_capability = {
        "（3）信道段参数": "信道频率规划",
        "（4）信道套参数": "信道业务参数",
        "1.组网参数分析": "组网信息分析",
        "2.点对点通信参数": "点对点业务参数",
        "3.虚拟子网参数": "虚拟子网参数",
    }

    # Group detailed errors by capability area
    errors_by_capability = {}
    for err in detailed_errors:
        section_title = err.get('section_title')
        capability_name = section_to_capability.get(section_title, section_title)  # Use friendly name if available
        if capability_name not in errors_by_capability:
            errors_by_capability[capability_name] = []
        errors_by_capability[capability_name].append(err)

    # --- Node Styles and Colors ---
    # zorder ensures drawing order: root on top, then main, then sub, arrows at bottom
    ROOT_STYLE = dict(fontsize=20, fontweight='bold', ha='center', va='center', color='white',
                      bbox=dict(boxstyle="round,pad=0.6", fc="#3F51B5", ec="#283593", lw=1.5, zorder=3))  # Indigo
    MAIN_STYLE = dict(fontsize=14, fontweight='bold', ha='left', va='center', color='#333333',
                      bbox=dict(boxstyle="round,pad=0.4", fc="#64B5F6", ec="#2196F3", lw=1.2, zorder=2))  # Light Blue
    SUB_STYLE = dict(fontsize=10, ha='left', va='top', color='#333333',  # va='top' for proper vertical stacking
                     bbox=dict(boxstyle="round,pad=0.3", fc="#E0F2F7", ec="#90CAF9", lw=0.8, alpha=0.9,
                               zorder=1))  # Lighter Blue
    NO_ERROR_STYLE = dict(fontsize=12, ha='center', va='center', color='#333333',
                          bbox=dict(boxstyle="round,pad=0.4", fc="#A5D6A7", ec="#66BB6A", lw=1, alpha=0.9,
                                    zorder=1))  # Light Green

    # Arrow Styles
    ARROW_COLOR_PRIMARY = "#607D8B"  # Darker grey for main connections
    ARROW_COLOR_SECONDARY = "#9E9E9E"  # Lighter grey for sub-connections

    # --- Positioning ---
    root_x, root_y = 0.5, 0.95  # Root node starting position (center of node)

    # Root Node
    root_text = f"{student_name} 的能力提升路线"
    root_node_obj = ax.text(root_x, root_y, root_text, **ROOT_STYLE)

    # Get bounding box of the root node in *data coordinates*
    root_bbox_display = root_node_obj.get_window_extent(renderer)
    root_bbox_data = root_bbox_display.transformed(ax.transData.inverted())

    # current_y_bottom_tracker keeps track of the lowest point occupied by any node
    # Initialize it to the bottom of the root node
    current_y_bottom_tracker = root_bbox_data.y0 - 0.05  # Start below the root node with some padding

    if not errors_by_capability:
        no_errors_text = "恭喜！您的答卷全部正确，表明您在所有评估领域都表现优秀，无需特定学习路线！"
        wrapped_text = "\n".join(textwrap.wrap(no_errors_text, width=60))

        no_error_node_obj = ax.text(root_x, current_y_bottom_tracker - 0.1, wrapped_text, **NO_ERROR_STYLE)
        no_error_bbox_display = no_error_node_obj.get_window_extent(renderer)
        no_error_bbox_data = no_error_bbox_display.transformed(ax.transData.inverted())

        ax.annotate('',
                    xy=(root_x, no_error_bbox_data.y1 + 0.01),
                    xytext=(root_x, root_bbox_data.y0 - 0.01),
                    arrowprops=dict(arrowstyle="->", color=ARROW_COLOR_PRIMARY, lw=2, connectionstyle="arc3,rad=0.0",
                                    zorder=0))

        current_y_bottom_tracker = no_error_bbox_data.y0 - 0.05

    else:
        capabilities_list = sorted(list(errors_by_capability.keys()))

        main_x_indent = 0.1  # X position for main branches (left-aligned)
        sub_x_indent = 0.28  # X position for sub-branches (indented further right)

        for i, capability in enumerate(capabilities_list):
            errors = errors_by_capability[capability]

            current_y_bottom_tracker -= 0.06  # Vertical spacing between main branches

            main_node_obj = ax.text(main_x_indent, current_y_bottom_tracker, capability, **MAIN_STYLE)
            main_bbox_display = main_node_obj.get_window_extent(renderer)
            main_bbox_data = main_bbox_display.transformed(ax.transData.inverted())

            ax.annotate('',
                        xy=(main_bbox_data.x0 + main_bbox_data.width / 2, main_bbox_data.y1 + 0.01),
                        xytext=(root_x, root_bbox_data.y0 - 0.01),
                        arrowprops=dict(arrowstyle="->", color=ARROW_COLOR_PRIMARY, lw=1.5,
                                        connectionstyle="arc3,rad=0.2" if i % 2 == 0 else "arc3,rad=-0.2", zorder=0))

            current_y_bottom_tracker = main_bbox_data.y0 - 0.02

            unique_recommendations = set()
            for error in errors:
                rec = get_study_recommendation(error)
                unique_recommendations.add(rec)

            sorted_recommendations = sorted(list(unique_recommendations))

            for j, rec_text in enumerate(sorted_recommendations):
                # Adjust width based on desired line length, can be dynamic if needed
                wrapped_rec = "\n".join(textwrap.wrap(rec_text, width=45))

                sub_node_obj = ax.text(sub_x_indent, current_y_bottom_tracker, wrapped_rec, **SUB_STYLE)
                sub_bbox_display = sub_node_obj.get_window_extent(renderer)
                sub_bbox_data = sub_bbox_display.transformed(ax.transData.inverted())

                ax.annotate('',
                            xy=(sub_bbox_data.x0 - 0.01, sub_bbox_data.y0 + sub_bbox_data.height / 2),
                            xytext=(main_bbox_data.x1 + 0.01, main_bbox_data.y0 + main_bbox_data.height / 2),
                            arrowprops=dict(arrowstyle="->", color=ARROW_COLOR_SECONDARY, lw=1.2,
                                            connectionstyle="arc3,rad=0.0", zorder=0))

                current_y_bottom_tracker = sub_bbox_data.y0 - 0.01

    # Set overall y-limits to fit all content with some padding
    ax.set_ylim(current_y_bottom_tracker - 0.05, root_y + root_bbox_data.height / 2 + 0.05)

    fig.tight_layout(rect=[0, 0, 1, 1])
    return fig, ax


# --- Main program entry point, example usage (kept for local testing) ---
if __name__ == '__main__':
    print("Running person_status.py examples locally...")

    # Example 1: Single Radar
    attributes_single = ['能力1', '能力2', '能力3', '能力4', '能力5', '能力6']
    values_single = np.array([75, 60, 85, 90, 70, 55])
    fig_single, ax_single = plot_attribute_radar("学员1", attributes_single, values_single)
    plt.show()

    # Example 2: History Radar (New!)
    student_history = [
        {'attributes': ['能力1', '能力2', '能力3', '能力4'], 'scores': [50, 60, 70, 80]},  # 1st submission
        {'attributes': ['能力1', '能力2', '能力3', '能力4'], 'scores': [60, 65, 75, 85]},  # 2nd submission
        {'attributes': ['能力1', '能力2', '能力3', '能力4'], 'scores': [70, 70, 80, 90]}  # 3rd submission
    ]
    fig_history, ax_history = plot_history_radar("测试学员历史", student_history)
    plt.show()

    # Example 3: Basic test for font setting (retained)
    attributes_font_test = ['中文属性一', '中文属性二', '中文属性三', '中文属性四', '中文属性五']
    values_font_test = np.array([80, 70, 90, 60, 75])
    fig_font, ax_font = plot_attribute_radar("测试学员", attributes_font_test, values_font_test, title="中文字体测试")
    plt.show()

    # Example 4: Study Route Mindmap (New!)
    sample_detailed_errors = [
        {'section_title': '（3）信道段参数', 'type': 'dropdown', 'field_label': '信道类型选择', 'user_value': 'xx',
         'answer_value': 'uu'},
        {'section_title': '（3）信道段参数', 'type': 'dataframe_cell', 'row': 1, 'col': 2,
         'col_header': '下行起始频率（khz）', 'user_value': '10.0', 'answer_value': 'uu 模式下，下行起始频率应在 12.25-12.75 范围内'},
        {'section_title': '（3）信道段参数', 'type': 'dataframe_cell', 'row': 1, 'col': 5,
         'col_header': '上行终止频率（khz）', 'user_value': '13.0', 'answer_value': 'uu 模式下，上行终止频率应在 14.0-14.5 范围内'},
        {'section_title': '（3）信道段参数', 'type': 'logic_check_failed', 'row': 1, 'col': 4,
         'col_header': '上行起始频率（khz）', 'user_value': '13.0', 'answer_value': 'uu 模式下应为 下行起始频率+1.75'},
        {'section_title': '（3）信道段参数', 'type': 'frequency_logic_error', 'row': 1, 'col_header_ul_end': '上行终止频率（khz）',
         'col_header_dl_start': '下行起始频率（khz）', 'user_value_ul_end': '13.00', 'user_value_dl_start': '12.00',
         'message': '上行终止频率 (13.00khz) 不应大于下行起始频率 (12.00khz)。'}, # NEW ERROR EXAMPLE
        {'section_title': '（4）信道套参数', 'type': 'dataframe_cell', 'row': 1, 'col': 2, 'col_header': 'TDM',
         'user_value': '5', 'answer_value': '10'},
        {'section_title': '1.组网参数分析', 'type': 'dataframe_duplicate', 'row': 3, 'col': 4, 'col_header': 'CC地址',
         'user_value': '192.168.1.100', 'message': "值 '192.168.1.100' 在此行重复出现。CC地址列不允许重复。"},
        {'section_title': '2.点对点通信参数', 'type': 'textbox', 'field_label': '本端CC地址',
         'user_value': '192.168.1.1', 'answer_value': '192.168.1.100'},
        {'section_title': '2.点对点通信参数', 'type': 'frequency_logic_error', 'row': 1, 'col_header_ul_end': '上行终止频点（khz）',
         'col_header_dl_start': '下行起始频点（khz）', 'user_value_ul_end': '5000.00', 'user_value_dl_start': '4000.00',
         'message': '上行终止频率 (5000.00khz) 不应大于下行起始频率 (4000.00khz)。'}, # NEW ERROR EXAMPLE
        {'section_title': '2.点对点通信参数', 'type': 'bandwidth_rate_mismatch', 'row': 1, 'col_header_rate': '速率kbps',
         'col_header_bandwidth': '带宽（khz）', 'user_value_rate': '1024', 'user_value_bandwidth': '1000',
         'answer_value_required_bandwidth': '1360',
         'message': '带宽 (1000khz) 小于速率 1024kbps 对应的最低要求带宽 (1360khz)。'}, # NEW ERROR EXAMPLE
        {'section_title': '3.虚拟子网参数', 'type': 'dataframe_format_error',
         'message': '虚拟子网参数表格格式错误或无法解析。'},
        {'section_title': '（4）信道套参数', 'type': 'dataframe_cell', 'row': 2, 'col': 3, 'col_header': 'ALOHA',
         'user_value': '20', 'answer_value': '15'}
    ]
    fig_mindmap, ax_mindmap = plot_study_route_mindmap("小明", sample_detailed_errors)
    plt.show()

    # Example 5: Study Route Mindmap with no errors
    fig_mindmap_no_error, ax_mindmap_no_error = plot_study_route_mindmap("优秀学员", [])
    plt.show()

    # Example 6: Overall Comparison Radar (New!)
    comparison_data = [
        ('学生A', [80, 70, 90, 60, 75, 85]),
        ('学生B', [70, 85, 65, 95, 80, 70]),
        ('学生C', [90, 75, 80, 70, 90, 60])
    ]
    common_attributes = ['信道频率规划', '信道业务参数', '组网信息分析', '点对点业务参数', '虚拟子网参数', '组内评价']
    fig_compare, ax_compare = plot_comparison_radar(comparison_data, common_attributes)
    plt.show()