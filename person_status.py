import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
from matplotlib.font_manager import FontProperties
import textwrap

try:
    font_paths = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    zh_font = None
    # 尝试多种常见的中文宋体或黑体字体名称，提高兼容性
    preferred_fonts = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'Arial Unicode MS', 'Noto Sans CJK SC']

    for font_name in preferred_fonts:
        try:
            # 尝试直接通过字体名称查找
            zh_font = matplotlib.font_manager.FontProperties(family=font_name)
            # 验证字体是否实际可用
            if os.path.exists(matplotlib.font_manager.findfont(font_name)):
                break
            else:
                zh_font = None  # 如果通过名称找到的路径不存在，则重置
        except Exception:
            # 如果直接通过名称查找失败，则尝试遍历文件路径
            for font_path in font_paths:
                fname = os.path.basename(font_path).lower()
                if font_name.lower().replace(" ", "") in fname.lower().replace(" ", ""):
                    zh_font = matplotlib.font_manager.FontProperties(fname=font_path)
                    break
            if zh_font:
                break  # 找到了就退出外层循环

    if zh_font:
        plt.rcParams['font.sans-serif'] = [zh_font.get_name()]
    else:
        print("Warning: Could not find common Chinese fonts. Falling back. Chinese labels might not display correctly.")
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'Arial Unicode MS',
                                           'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
except Exception as e:
    print(f"Error setting Chinese font in person_status.py: {e}")
    print("Chinese labels might not display correctly.")


def plot_attribute_radar(character_name, attributes, values,
                         max_value=100, color='skyblue', title=None, figsize=(8, 8)):
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
    fig.tight_layout(rect=[0, 0, 0.95, 1])

    return fig, ax


def plot_history_radar(student_name, submissions, max_value=100, figsize=(9, 9)):
    if not submissions:
        raise ValueError("没有提交记录可用于绘制成长雷达图。")
    if len(submissions[0]['attributes']) < 3:
        raise ValueError("至少需要3个能力维度才能绘制雷达图。")

    num_attributes = len(submissions[0]['attributes'])
    attributes = submissions[0]['attributes']

    angles = np.linspace(0, 2 * np.pi, num_attributes, endpoint=False).tolist()
    plot_angles = angles + angles[:1]

    try:
        from matplotlib import colormaps as cmaps
        cmap = cmaps.get_cmap('tab10')
    except (ImportError, AttributeError):
        import matplotlib.cm as cm
        cmap = cm.get_cmap('tab10')

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    for i, submission in enumerate(submissions):
        scores = submission['scores']
        plot_values = np.concatenate((np.array(scores), [scores[0]]))

        if len(submissions) > 1:
            color = cmap(i / (len(submissions) - 1))
        else:
            color = cmap(0.5)

        ax.plot(plot_angles, plot_values,
                linewidth=2, linestyle='solid',
                label=f'第{i + 1}次提交',
                color=color)
        ax.fill(plot_angles, plot_values, color, alpha=0.3)

    ax.set_xticks(angles)
    ax.set_xticklabels(attributes)
    ax.set_yticks(np.arange(0, max_value + 10, 10))
    ax.set_ylim(0, max_value)
    ax.set_rlabel_position(0)
    ax.grid(True, linestyle='--', alpha=0.7)

    ax.set_title(f'{student_name} 最近{len(submissions)}次能力变化图', size=16, y=1.08)
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1.0), frameon=False)
    fig.tight_layout(rect=[0, 0, 0.95, 1])

    return fig, ax


def plot_comparison_radar(list_of_name_and_scores, attributes, max_value=100, figsize=(9, 9)):
    if not list_of_name_and_scores or len(list_of_name_and_scores) < 2:
        raise ValueError("至少需要两位学生的数据才能绘制总体能力对比图。")
    if not attributes or len(attributes) < 3:
        raise ValueError("至少需要3个能力维度才能绘制雷达图。")

    num_attributes = len(attributes)
    angles = np.linspace(0, 2 * np.pi, num_attributes, endpoint=False).tolist()
    plot_angles = angles + angles[:1]

    try:
        from matplotlib import colormaps as cmaps
        cmap = cmaps.get_cmap('tab10')
    except (ImportError, AttributeError):
        import matplotlib.cm as cm
        cmap = cm.get_cmap('tab10')

    colors_list = [cmap(i / (len(list_of_name_and_scores) - 1)) if len(list_of_name_and_scores) > 1 else cmap(0.5) for i
                   in range(len(list_of_name_and_scores))]

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    for i, (student_name, scores) in enumerate(list_of_name_and_scores):
        plot_val = np.concatenate((np.array(scores), [scores[0]]))
        color = colors_list[i % len(colors_list)]

        ax.plot(plot_angles, plot_val, linewidth=2, linestyle='solid', label=student_name, color=color)
        ax.fill(plot_angles, plot_val, color, alpha=0.3)

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
    ax.set_title("总体能力对比", size=16, y=1.08)
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1.0), frameon=False)
    fig.tight_layout(rect=[0, 0, 0.95, 1])

    return fig, ax


# --- 新增：绘制学习路线思维导图函数 ---

# 定义错误类型到通用学习建议的映射 (更详细和全面的映射可以进一步扩展)
RECOMMENDATIONS_MAP = {
    # （3）信道段参数 - 信道频率规划
    # 移除信道类型选择的建议
    # ("（3）信道段参数", "dropdown", "信道类型选择"): "复习信道类型（'uu'/'aa'）的选择与意义。确保选择正确，才能进行后续频率逻辑检查。",
    ("（3）信道段参数", "dataframe_cell",
     "下行起始频率应在"): "检查下行起始频率是否在指定范围内（'uu'模式12.25-12.75MHz，'aa'模式19.6-21.2MHz）。",
    ("（3）信道段参数", "dataframe_cell",
     "下行终止频率应在"): "检查下行终止频率是否在指定范围内（'uu'模式12.25-12.75MHz，'aa'模式19.6-21.2MHz）。",
    ("（3）信道段参数", "dataframe_cell",
     "上行起始频率应在"): "检查上行起始频率是否在指定范围内（'uu'模式14.0-14.5MHz，'aa'模式29.4-31.0MHz）。",
    ("（3）信道段参数", "dataframe_cell",
     "上行终止频率应在"): "检查上行终止频率是否在指定范围内（'uu'模式14.0-14.5MHz，'aa'模式29.4-31.0MHz）。",
    ("（3）信道段参数", "logic_check_failed",
     "不满足"): "检查上行起始/终止频率与下行起始/终止频率是否保持正确的偏移关系（'uu'模式+1.75MHz，'aa'模式+9.8MHz）。",
    ("（3）信道段参数", "frequency_logic_error",
     "上行终止频率"): "信道段上行终止频率不应大于下行起始频率，请核对频率分配逻辑。",
    ("（3）信道段参数", "dataframe_format_error",
     None): "确保信道段参数表格格式正确，所有频率值均以数字填写，且表格结构完整。",
    ("（3）信道段参数", "data_type_error", "频率值应为数字"): "信道段频率值必须是数字，请检查输入格式。",
    ("（3）信道段参数", "column_count_mismatch", None): "信道段参数表格列数不匹配，请核对表格结构。",
    ("（3）信道段参数", "logic_check_failed",
     "无法对信道类型"): "信道段频率逻辑检查依赖于信道类型，请确保信道类型为'uu'或'aa'。",

    # （4）信道套参数 - 信道业务参数 (UPDATED RECOMMENDATIONS)
    ("（4）信道套参数", "dataframe_format_error",
     None): "信道套参数表格格式错误或行/列数不匹配，应为2行5列，请核对表格结构及内容。",
    ("（4）信道套参数", "logic_check_failed",
     "无法获取信道段参数中的频率数据"): "信道套参数中的频点校验依赖信道段参数，请检查信道段参数表格的填写。",
    ("（4）信道套参数", "logic_check_failed",
     "无法校验TDM中心频点"): "因信道段频率数据缺失或格式错误，无法校验TDM中心频点。请先修正信道段参数。",
    ("（4）信道套参数", "logic_check_failed",
     "无法校验ALOHA中心频点"): "因信道段频率数据缺失或格式错误，无法校验ALOHA中心频点。请先修正信道段参数。",

    ("（4）信道套参数", "data_type_error", "速率"): "信道套参数中，速率应为数字，请检查输入。",
    ("（4）信道套参数", "dataframe_cell", "速率应为 9.6"): "信道套参数中，速率应固定为9.6kbps，请核对。",

    ("（4）信道套参数", "data_type_error", "带宽"): "信道套参数中，带宽应为数字，请检查输入。",
    ("（4）信道套参数", "dataframe_cell", "带宽应为 100"): "信道套参数中，带宽应固定为100kHz，请核对。",

    ("（4）信道套参数", "data_type_error", "上行中心频点"): "信道套参数中，上行中心频点应为数字，请检查输入。",
    ("（4）信道套参数", "dataframe_cell",
     "上行中心频点应为"): "上行中心频点应根据信道段参数计算（TDM：信道段上行起始频率+50；ALOHA：信道段上行起始频率+150）。",

    ("（4）信道套参数", "data_type_error", "下行中心频点"): "信道套参数中，下行中心频点应为数字，请检查输入。",
    ("（4）信道套参数", "dataframe_cell",
     "下行中心频点应为"): "下行中心频点应根据信道段参数计算（TDM：信道段下行起始频率+50；ALOHA：信道段下行起始频率+150）。",

    # 1.组网参数分析 - 组网信息分析
    ("1.组网参数分析", "dataframe_duplicate",
     "CC地址列不允许重复"): "深入学习CC地址规划规范，确保每台通信控制器（CC）的地址是唯一的。",
    ("1.组网参数分析", "dataframe_format_error", None): "检查组网参数分析表格的整体格式，确保数据可被正确解析。",
    ("1.组网参数分析", "column_count_mismatch",
     "CC地址列"): "组网参数分析表格缺少CC地址列，无法进行重复性校验。请核对表格结构。",

    # 2.点对点通信参数 - 点对点业务参数
    ("2.点对点通信参数", "textbox", "本端CC地址"): "核对本端CC地址的正确填写格式和值。",
    ("2.点对点通信参数", "textbox", "对端XX地址"): "核对对端XX地址的正确填写格式和值。",
    ("2.点对点通信参数", "dataframe_cell", None): "复习点对点业务参数（速率、带宽、频率范围）的配置要求。",
    ("2.点对点通信参数", "frequency_logic_error",
     "上行终止频率"): "点对点通信上行终止频率不应大于下行起始频率，请核对频点配置。",
    ("2.点对点通信参数", "bandwidth_rate_mismatch",
     "小于速率"): "请根据速率（kbps）检查带宽（khz）是否满足KBP映射文件中定义的最低要求，确保带宽大于等于对应值。",
    ("2.点对点通信参数", "kbp_load_error", None): "KBP映射文件加载失败或为空，请检查kbp.txt文件是否存在和格式是否正确。",
    ("2.点对点通信参数", "row_count_mismatch", None): "核对点对点通信参数表格行数是否完整。",
    ("2.点对点通信参数", "column_count_mismatch", None): "检查点对点通信参数表格的列数是否正确。",
    ("2.点对点通信参数", "dataframe_format_error", None): "确保点对点通信参数表格格式正确。",

    # 3.虚拟子网参数 - 虚拟子网参数 (UPDATED RECOMMENDATIONS)
    ("3.虚拟子网参数", "dataframe_format_error",
     None): "虚拟子网参数表格格式错误或行/列数不匹配。应为1行6列，请核对表格结构及内容。",
    ("3.虚拟子网参数", "logic_check_failed", "请选择一个虚拟子网速率"): "请在下拉列表中选择一个速率，以便校验带宽。",
    ("3.虚拟子网参数", "bandwidth_rate_mismatch",
     "小于速率"): "虚拟子网带宽应大于或等于所选速率对应的KBP最低带宽，请核对。",
    ("3.虚拟子网参数", "data_type_error", "速率或带宽"): "虚拟子网速率或带宽应为数字，请检查输入格式。",
    ("3.虚拟子网参数", "frequency_logic_error",
     "下行起始频率不能大于下行终止频率"): "虚拟子网下行频率范围起始值不能大于终止值，请检查。",
    ("3.虚拟子网参数", "frequency_logic_error",
     "上行起始频率不能大于上行终止频率"): "虚拟子网上行频率范围起始值不能大于终止值，请检查。",
    ("3.虚拟子网参数", "frequency_logic_error",
     "频率范围重叠"): "虚拟子网的下行频率范围与上行频率范围不允许重叠，请调整。",
    ("3.虚拟子网参数", "data_type_error", "频率值应为数字"): "虚拟子网频率值必须是数字，请检查输入格式。",

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
    raw_message = detailed_error.get('message', '')
    col_header = detailed_error.get('col_header')

    # 将具体的错误消息归类为通用提示，以便匹配 RECOMMENDATIONS_MAP
    specific_hint = None
    if error_type == 'dataframe_cell':
        if "应为数字" in raw_message:
            specific_hint = f"{col_header}应为数字"  # "TDM速率应为数字"
        elif "应为" in raw_message:  # "TDM速率应为 9.6"
            specific_hint = raw_message.split("应为")[0] + "应为"
        else:  # Fallback for other dataframe_cell messages
            specific_hint = raw_message
    elif error_type == 'textbox':
        specific_hint = detailed_error.get('field_label')
    elif error_type == 'dropdown':
        specific_hint = detailed_error.get('field_label')
    elif error_type == 'logic_check_failed':
        if "无法对信道类型" in raw_message:
            specific_hint = "无法对信道类型"
        elif "无法获取信道段参数中的频率数据" in raw_message:
            specific_hint = "无法获取信道段参数中的频率数据"
        elif "无法校验TDM中心频点" in raw_message:  # New specific message for channel suite logic failure
            specific_hint = "无法校验TDM中心频点"
        elif "无法校验ALOHA中心频点" in raw_message:  # New specific message for channel suite logic failure
            specific_hint = "无法校验ALOHA中心频点"
        elif "不满足" in raw_message and "偏移关系" in raw_message:
            specific_hint = "不满足"  # For offset relationship
        else:
            specific_hint = raw_message
    elif error_type in ['frequency_logic_error', 'bandwidth_rate_mismatch', 'kbp_load_error', 'dataframe_duplicate',
                        'data_type_error', 'column_count_mismatch', 'row_count_mismatch']:
        if "CC地址列不允许重复" in raw_message:
            specific_hint = "CC地址列不允许重复"
        elif "小于速率" in raw_message:
            specific_hint = "小于速率"
        elif "频率范围重叠" in raw_message:
            specific_hint = "频率范围重叠"
        elif "下行起始频率不能大于下行终止频率" in raw_message:
            specific_hint = "下行起始频率不能大于下行终止频率"
        elif "上行起始频率不能大于上行终止频率" in raw_message:
            specific_hint = "上行起始频率不能大于上行终止频率"
        elif "应为数字" in raw_message:
            specific_hint = "频率值应为数字"  # Group all frequency data type errors
        elif "列数不足" in raw_message:
            if "CC地址列" in raw_message:
                specific_hint = "CC地址列"  # specific for network analysis
            else:
                specific_hint = None  # General column mismatch covered by (section, type, None)
        elif "表格行数不匹配" in raw_message:
            specific_hint = None  # General row mismatch covered by (section, type, None)
        else:
            specific_hint = raw_message  # Fallback to raw message if none of the above

    # 尝试最具体的匹配 (section, type, specific_hint)
    if (section_title, error_type, specific_hint) in RECOMMENDATIONS_MAP:
        return RECOMMENDATIONS_MAP[(section_title, error_type, specific_hint)]

    # 尝试次具体匹配 (section, type, None)
    if (section_title, error_type, None) in RECOMMENDATIONS_MAP:
        return RECOMMENDATIONS_MAP[(section_title, error_type, None)]

    # 尝试最通用匹配 (None, type, None)
    if (None, error_type, None) in RECOMMENDATIONS_MAP:
        return RECOMMENDATIONS_MAP[(None, error_type, None)]

    return f"针对 '{section_title}' 部分的 '{raw_message}' 错误，建议复习相关知识点。"


def plot_study_route_mindmap(student_name, detailed_errors, figsize=(12, 10)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("#fcfcfc")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    section_to_capability = {
        "（3）信道段参数": "信道频率规划",
        "（4）信道套参数": "信道业务参数",
        "1.组网参数分析": "组网信息分析",
        "2.点对点通信参数": "点对点业务参数",
        "3.虚拟子网参数": "虚拟子网参数",
    }

    errors_by_capability = {}
    for err in detailed_errors:
        section_title = err.get('section_title')
        capability_name = section_to_capability.get(section_title, section_title)
        if capability_name not in errors_by_capability:
            errors_by_capability[capability_name] = []
        errors_by_capability[capability_name].append(err)

    ROOT_STYLE = dict(fontsize=20, fontweight='bold', ha='center', va='center', color='white',
                      bbox=dict(boxstyle="round,pad=0.6", fc="#3F51B5", ec="#283593", lw=1.5, zorder=3))
    MAIN_STYLE = dict(fontsize=14, fontweight='bold', ha='left', va='center', color='#333333',
                      bbox=dict(boxstyle="round,pad=0.4", fc="#64B5F6", ec="#2196F3", lw=1.2, zorder=2))
    SUB_STYLE = dict(fontsize=10, ha='left', va='top', color='#333333',
                     bbox=dict(boxstyle="round,pad=0.3", fc="#E0F2F7", ec="#90CAF9", lw=0.8, alpha=0.9,
                               zorder=1))
    NO_ERROR_STYLE = dict(fontsize=12, ha='center', va='center', color='#333333',
                          bbox=dict(boxstyle="round,pad=0.4", fc="#A5D6A7", ec="#66BB6A", lw=1, alpha=0.9,
                                    zorder=1))

    ARROW_COLOR_PRIMARY = "#607D8B"
    ARROW_COLOR_SECONDARY = "#9E9E9E"

    root_x, root_y = 0.5, 0.95

    root_text = f"{student_name} 的能力提升路线"
    root_node_obj = ax.text(root_x, root_y, root_text, **ROOT_STYLE)

    root_bbox_display = root_node_obj.get_window_extent(renderer)
    root_bbox_data = root_bbox_display.transformed(ax.transData.inverted())

    current_y_bottom_tracker = root_bbox_data.y0 - 0.05

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

        main_x_indent = 0.1
        sub_x_indent = 0.28

        for i, capability in enumerate(capabilities_list):
            errors = errors_by_capability[capability]

            current_y_bottom_tracker -= 0.06

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

    ax.set_ylim(current_y_bottom_tracker - 0.05, root_y + root_bbox_data.height / 2 + 0.05)

    fig.tight_layout(rect=[0, 0, 1, 1])
    return fig, ax