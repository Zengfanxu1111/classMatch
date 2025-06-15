import gradio as gr
import pandas as pd
import tempfile
import os
import numpy as np
import os

print("当前工作目录:", os.getcwd())
print("文件是否存在:", os.path.exists("static/slide.html"))
# Import checker.py and analyzer.py functions
from checker import capture_paper_data_string, check_paper, _SUBNET_ID_LABEL, _NETWORK_NAME_LABEL, \
    _LOCAL_CC_ADDRESS_LABEL, _REMOTE_XX_ADDRESS_LABEL, _CHANNEL_TYPE_LABEL, _KBP_MAPPING, _CHANNEL_SUITE_HEADERS

from analyzer import \
    perform_analysis_and_plot_radar

from person_status import plot_attribute_radar, plot_history_radar, plot_study_route_mindmap, plot_comparison_radar
import matplotlib.pyplot as plt
import matplotlib.cm as cm

try:
    from matplotlib import colormaps as cmaps
    _use_new_cmaps = True
except (ImportError, AttributeError):
    _use_new_cmaps = True
    print("Warning: Could not import matplotlib.colormaps directly. Falling back to matplotlib.cm or default cycle.")

STUDENT_DATA = {}
MAX_SUBMISSIONS_HISTORY = 5

QUIZ_QUESTIONS = [
    {
        "id": "q1",
        "question": "1. 以下哪个选项是表示网络中某个特定设备的唯一标识符？",
        "options": ["IP地址", "子网掩码", "网关", "DNS服务器"],
        "correct_answer": "IP地址"
    },
    {
        "id": "q2",
        "question": "2. 在TCP/IP协议簇中，负责逻辑寻址的协议是？",
        "options": ["ARP", "ICMP", "IP", "TCP"],
        "correct_answer": "IP"
    },
    {
        "id": "q3",
        "question": "3. 卫星通信中，下行频率通常指哪个方向的频率？",
        "options": ["地面站到卫星", "卫星到地面站", "卫星到卫星", "地面站之间"],
        "correct_answer": "卫星到地面站"
    },
    {
        "id": "q4",
        "question": "4. TDM（时分复用）技术的主要优点是什么？",
        "options": ["提高频率利用率", "提高带宽利用率", "减少传输延迟", "实现多路信号共享同一传输介质"],
        "correct_answer": "实现多路信号共享同一传输介质"
    },
    {
        "id": "q5",
        "question": "5. 在组网参数分析中，CC地址的主要作用是什么？",
        "options": ["表示设备型号", "用于唯一标识通信控制器", "指示设备位置", "提供电话号码"],
        "correct_answer": "用于唯一标识通信控制器"
    }
]

quiz_stats = {
    q["id"]: {"correct_count": 0, "total_attempts": 0} for q in QUIZ_QUESTIONS
}


def submit_quiz(*user_answers):
    global quiz_stats
    score = 0
    results_md = "### 随堂测试结果\n\n"
    detailed_feedback = []

    for i, question_data in enumerate(QUIZ_QUESTIONS):
        q_id = question_data["id"]
        correct_answer = question_data["correct_answer"]
        user_answer = user_answers[i]

        quiz_stats[q_id]["total_attempts"] += 1

        if user_answer == correct_answer:
            score += 1
            quiz_stats[q_id]["correct_count"] += 1
            detailed_feedback.append(f"Q{i + 1}. **正确!** 您的答案: `{user_answer}`")
        else:
            detailed_feedback.append(f"Q{i + 1}. 错误. 您的答案: `{user_answer}` (正确答案: `{correct_answer}`)")

    results_md += f"您本次测试的得分是： **{score} / {len(QUIZ_QUESTIONS)}**\n\n"
    results_md += "#### 详细反馈：\n"
    results_md += "\n".join(detailed_feedback)

    stats_md = display_quiz_stats()

    return gr.update(value=results_md, visible=True), gr.update(value=stats_md, visible=True)


def display_quiz_stats():
    stats_md = "### 题目统计\n\n"
    stats_md += "（统计数据会随每次提交更新，应用重启后重置）\n\n"
    for i, question_data in enumerate(QUIZ_QUESTIONS):
        q_id = question_data["id"]
        correct = quiz_stats[q_id]["correct_count"]
        total = quiz_stats[q_id]["total_attempts"]

        correct_percentage = (correct / total * 100) if total > 0 else 0

        stats_md += f"Q{i + 1}. **{question_data['question']}**\n"
        stats_md += f"   - 正确人数: {correct}\n"
        stats_md += f"   - 总尝试人数: {total}\n"
        stats_md += f"   - 正确率: {correct_percentage:.2f}%\n\n"
    return stats_md

station_config_headers = ["用户单位", "站名", "站型", "站地址", "站位置", "设备序列号"]
station_config_data = [
    ["单位1", "", "", "", "", "1111"],
    ["单位2", "", "", "", "", "2222"],
    ["单位3", "", "", "", "", "3333"],
    ["单位4", "", "", "", "", "4444"],
    ["单位5", "", "", "", "", "5555"],
]

channel_segment_headers = ["卫星名称", "下行起始频率（khz）", "下行终止频率（khz）", "上行起始频率（khz）",
                           "上行终止频率（khz）"]
channel_segment_data = [
    ["", "", "", "", ""],
]

# 修改信道套参数的表头和数据以匹配新的3x5表格样式
channel_suite_headers = _CHANNEL_SUITE_HEADERS # 从checker.py导入，确保一致性
channel_suite_data = [
    ["TDM", "", "", "", ""],
    ["ALOHA", "", "", "", ""],
]

network_analysis_headers = ["用户单位", "站型", "站地址", "CC地址", "电话号码", "设备序列号"]
network_analysis_data = [
    ["单位1", "", "", "", "", "1111"],
    ["单位2", "", "", "", "", "2222"],
    ["单位3", "", "", "", "", "3333"],
    ["单位4", "", "", "", "", "4444"],
    ["单位5", "", "", "", "", "5555"],
    ["单位6", "", "", "", "", "4444"],
    ["单位7", "", "", "", "", "5555"],
    ["单位8", "", "", "", "", "3333"],
    ["单位9", "", "", "", "", "4444"],
    ["单位10", "", "", "", "", "5555"],
    ["单位11", "", "", "", "", "4444"],
    ["单位12", "", "", "", "", "5555"],
]

p2p_headers = ["名称", "速率kbps", "带宽（khz）", "下行起始频点（khz）", "下行终止频点（khz）", "上行起始频点（khz）",
               "上行终止频点（khz）"]
p2p_data = [
    ["发送", "", "", "", "", "", ""],
    ["接收", "", "", "", "", "", ""],
]

virtual_subnet_headers = ["名称", "带宽（khz）", "下行起始频率（khz）", "下行终止频率（khz）", "上行起始频率（khz）",
                          "上行终止频率（khz）"]
virtual_subnet_data = [
    ["虚拟子网信道段", "", "", "", "", ""],
]


def _calculate_radar_data(error_sections_with_counts, peer_review_score):
    capability_definitions = {
        # "信道频率规划" 的 total_items is 7 (4 range checks + 2 offset checks + 1 new rule check (UL_End > DL_Start))
        "信道频率规划": {"full_title": "信道频率规划（下行、上行起始/终止频率）", "total_items": 7,
                         "original_titles": ["（3）信道段参数"]},
        # 信道业务参数现在有2行数据，每行4个可填写单元格（速率、带宽、上行频点、下行频点），总计8个可校验点
        "信道业务参数": {"full_title": "信道业务参数配置（TDM/ALOHA参数、速率、中心频点、带宽）", "total_items": 8,
                         "original_titles": ["（4）信道套参数"]},
        "组网信息分析": {"full_title": "组网信息分析（站型、站地址、CC地址、电话号码）", "total_items": len(network_analysis_data), # Updated: reflects the 12 rows checked for CC address duplication
                         "original_titles": ["1.组网参数分析"]},
        "点对点业务参数": {"full_title": "点对点业务参数配置（本端/对端地址、速率、带宽、频率）", "total_items": 4, # 2 rows * (1 freq rule + 1 bandwidth rule) = 4
                           "original_titles": ["2.点对点通信参数"]},
        "虚拟子网参数": {"full_title": "虚拟子网参数配置（带宽、频率、速率选择）", "total_items": 2, # 1 bandwidth rule + 1 frequency overlap rule
                         "original_titles": ["3.虚拟子网参数"]}
    }

    radar_attributes = []
    radar_scores = []

    for radar_key, definition in capability_definitions.items():
        radar_attributes.append(definition["full_title"].split("（")[0])
        total_items = definition.get("total_items", 0)

        if total_items == 0:
            score = 0
        else:
            error_count_value_from_checker = 0
            for error_title_from_checker, error_count_value in error_sections_with_counts:
                if error_title_from_checker in definition["original_titles"]:
                    if isinstance(error_count_value, int):
                        error_count_value_from_checker = error_count_value
                    else:
                        # Fallback if error count is not an int (e.g., format error)
                        error_count_value_from_checker = total_items
                    break

            correct_items = total_items - error_count_value_from_checker
            score = (correct_items / total_items) * 100
            score = max(0, min(score, 100))

        radar_scores.append(score)

    radar_attributes.append("组内评价")
    if peer_review_score is not None:
        radar_scores.append(max(0, min(peer_review_score, 100)))
    else:
        radar_scores.append(0)

    if len(radar_attributes) < 3 or not radar_scores or len(radar_attributes) != len(radar_scores):
        print("Warning: Calculated radar data is insufficient or inconsistent.")
        return [], []

    return radar_attributes, radar_scores


def _process_peer_review_scores(score_inputs):
    valid_peer_scores = []
    for score in score_inputs:
        if score is not None:
            try:
                s_float = float(score)
                if 0 <= s_float <= 100:
                    valid_peer_scores.append(s_float)
            except ValueError:
                pass
    return sum(valid_peer_scores) / len(valid_peer_scores) if valid_peer_scores else None


def _generate_analysis_report(error_sections_with_counts, average_peer_score):
    analysis_message_parts = ["能力分析结果："]
    identified_areas_text = []
    parsing_issue_sections = []

    if not error_sections_with_counts:
        analysis_message_parts.append("答卷全部正确，表明您在所有评估领域的能力都表现优秀！")
    else:
        analysis_message_parts.append("根据答卷中的错误部分，您的能力可能在以下方面需要加强：")
        for title, count in error_sections_with_counts:
            if isinstance(count, int):
                identified_areas_text.append(f"{title} (错误: {count})")
            else:
                identified_areas_text.append(f"{title} ({count})")
                parsing_issue_sections.append(title)

        if identified_areas_text:
            analysis_message_parts.append("- " + "\n- ".join(identified_areas_text))

    if parsing_issue_sections:
        analysis_message_parts.append("\n**重要提示:** 以下部分由于格式错误或解析失败，未能进行精确错误计数。")
        analysis_message_parts.append("请检查这些部分的填写格式是否与要求一致。")

    if average_peer_score is not None:
        analysis_message_parts.append(f"\n组内评价平均得分：{average_peer_score:.2f}")
    else:
        analysis_message_parts.append("\n未提供有效的组内评价分数。")

    return "\n".join(analysis_message_parts)


def _format_detailed_errors_markdown(detailed_errors, error_sections_with_counts):
    detailed_errors_md_string = "### 详细错误列表\n\n"
    if not detailed_errors:
        if not any(isinstance(count, int) and count > 0 for _, count in
                   error_sections_with_counts):
            detailed_errors_md_string += "恭喜，答卷主要内容正确，没有详细错误信息需要列出。"
        else:
            detailed_errors_md_string += "未能获取详细错误信息（可能由于答卷格式错误导致无法解析或无需提供）。"
    else:
        errors_by_section = {}
        for err in detailed_errors:
            section_title = err.get('section_title', '未知部分')
            if section_title not in errors_by_section:
                errors_by_section[section_title] = []
            errors_by_section[section_title].append(err)

        for section_title, errors in errors_by_section.items():
            detailed_errors_md_string += f"#### {section_title}\n\n"
            for err in errors:
                error_type = err.get('type')
                error_message = err.get('message', '无具体错误描述。')

                if error_type == 'textbox':
                    field_label = err.get('field_label', '未知字段').strip('：')
                    detailed_errors_md_string += f"- **'{field_label}'** 填写错误: 您的答案是 `{err['user_value']}`，标准答案是 `{err['answer_value']}`\n"
                elif error_type == 'dataframe_cell':
                    row_idx = err.get('row', -1)
                    col_header = err.get('col_header', f"列 {err.get('col', -1)}")
                    detailed_errors_md_string += f"- **表格错误** (行 {row_idx}, {col_header}): {error_message} 您的答案是 `{err['user_value']}`，标准答案是 `{err['answer_value']}`\n"
                elif error_type == 'dataframe_duplicate':
                    row_idx = err.get('row', -1)
                    col_header = err.get('col_header', f"列 {err.get('col', -1)}")
                    user_value = err.get('user_value', 'N/A')
                    detailed_errors_md_string += f"- **表格错误** (行 {row_idx}, {col_header}): 值 `{user_value}` {error_message}\n"
                elif error_type == 'dropdown':
                    field_label = err.get('field_label', '未知下拉项').strip('：')
                    detailed_errors_md_string += f"- **'{field_label}'** 选择错误: 您的选择是 `{err['user_value']}`，标准答案是 `{err['answer_value']}`\n"
                elif error_type == 'row_count_mismatch':
                    detailed_errors_md_string += f"- **表格行数错误**: {error_message} (您的行数: {err['user_value']}, 正确行数: {err['answer_value']})\n"
                elif error_type == 'column_count_mismatch':
                    row_idx = err.get('row', -1)
                    detailed_errors_md_string += f"- **表格列数错误** (行 {row_idx}): {error_message}\n"
                elif error_type == 'dataframe_format_error':
                    detailed_errors_md_string += f"- **表格格式错误**: {error_message}\n"
                elif error_type == 'data_type_error':
                    detailed_errors_md_string += f"- **数据类型错误**: {error_message}\n"
                elif error_type == 'logic_check_failed':
                    detailed_errors_md_string += f"- **逻辑检查失败**: {error_message}\n"
                elif error_type == 'frequency_logic_error':
                    row_idx = err.get('row', -1)
                    if 'user_value_ul_end' in err:
                        user_ul_end = err.get('user_value_ul_end', 'N/A')
                        user_dl_start = err.get('user_value_dl_start', 'N/A')
                        ul_end_header = err.get('col_header_ul_end', '上行终止频率')
                        dl_start_header = err.get('col_header_dl_start', '下行起始频率')
                        detailed_errors_md_string += f"- **频率逻辑错误** (行 {row_idx}, {ul_end_header} vs {dl_start_header}): {error_message} (您的上行终止频率: `{user_ul_end}`, 下行起始频率: `{user_dl_start}`)\n"
                    else:
                        detailed_errors_md_string += f"- **频率逻辑错误** (行 {row_idx}): {error_message}\n"
                elif error_type == 'bandwidth_rate_mismatch':
                    row_idx = err.get('row', -1)
                    user_rate = err.get('user_value_rate', 'N/A')
                    user_bandwidth = err.get('user_value_bandwidth', 'N/A')
                    detailed_errors_md_string += f"- **带宽与速率不匹配错误** (行 {row_idx}, 速率: `{user_rate}`, 带宽: `{user_bandwidth}`): {error_message}\n"
                elif error_type == 'kbp_load_error':
                    detailed_errors_md_string += f"- **配置错误**: {error_message}\n"
                elif error_type == 'unsupported_check_type':
                     detailed_errors_md_string += f"- **不支持的检查类型**: {error_message}\n"

            detailed_errors_md_string += "\n"
    return detailed_errors_md_string


def process_submission(
        student_name_value,
        subnet_id_value, network_name_value, station_config_value, channel_segment_value,
        channel_suite_value, network_analysis_value, local_cc_address_value,
        remote_xx_address_value, p2p_value, virtual_subnet_value,
        channel_type_value,
        virtual_subnet_rate_value,
        score1_value, score2_value, score3_value, score4_value, score5_value
):
    """
    Processes a student's submission, performs checks, generates analysis,
    stores data, and updates UI components.
    """
    download_file_output_update = gr.update(value=None, visible=False)
    check_result_md_output_update = gr.update(value="等待提交...")
    analysis_output_md_update = gr.update(value="等待提交...")
    single_student_radar_display_update = gr.update(value=None, visible=False)
    detailed_errors_output_update = gr.update(value="等待提交...")
    study_route_mindmap_display_update = gr.update(value=None, visible=False)
    student_list_choices_update = gr.update(choices=list(STUDENT_DATA.keys()), value=None, interactive=True)
    overall_radar_visibility_update = gr.update(visible=False, interactive=True)
    growth_radar_visibility_update = gr.update(visible=False, interactive=True)
    comparison_radar_display_update = gr.update(value=None, visible=False)
    selected_student_info_md_update = gr.update(
        value="请从下拉列表中选择一个学生查看能力图谱，或点击按钮查看总体能力对比图。")
    final_eval_student_name_display_update = gr.update(value="")
    ### 新增: 初始化CC地址错误信息更新
    network_analysis_error_md_update = gr.update(value="", visible=False)
    ### 结束新增

    student_name = student_name_value.strip()
    if not student_name:
        check_result_md_output_update = gr.update(value="**错误：请先输入您的姓名！**")
        return (download_file_output_update, check_result_md_output_update, analysis_output_md_update,
                single_student_radar_display_update, detailed_errors_output_update,
                study_route_mindmap_display_update, # 确保 study_route_mindmap_display 也在返回列表中
                student_list_choices_update, overall_radar_visibility_update, growth_radar_visibility_update,
                selected_student_info_md_update, comparison_radar_display_update,
                final_eval_student_name_display_update,
                network_analysis_error_md_update) # 更新返回


    temp_file_path = None
    try:
        user_output_string = capture_paper_data_string(
            subnet_id_value, network_name_value, station_config_headers, station_config_value,
            channel_segment_headers, channel_segment_value, channel_suite_headers, channel_suite_value,
            network_analysis_headers, network_analysis_value, local_cc_address_value,
            remote_xx_address_value, p2p_headers, p2p_value, virtual_subnet_headers, virtual_subnet_value,
            channel_type_value
        )
        with tempfile.NamedTemporaryFile(mode='w+', suffix=".txt", delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(user_output_string)
            temp_file_path = tmp_file.name
        download_file_output_update = gr.update(value=temp_file_path, label="下载答卷结果", visible=True)
    except Exception as e:
        print(f"Error saving file: {e}")
        download_file_output_update = gr.update(label=f"保存文件失败: {e}", visible=True, value=None)

    check_message_string, error_sections_with_counts, _, detailed_errors = check_paper(
        subnet_id_value, network_name_value, station_config_value, channel_segment_value, channel_type_value,
        channel_suite_value, network_analysis_value, local_cc_address_value, remote_xx_address_value,
        p2p_value, virtual_subnet_value, virtual_subnet_rate_value
    )

    ### 新增：检查CC地址重复错误
    cc_address_duplicate_found = False
    for err in detailed_errors:
        if err.get('type') == 'dataframe_duplicate' and \
           err.get('section_title') == '1.组网参数分析' and \
           err.get('col_header') == 'CC地址':
            cc_address_duplicate_found = True
            break

    if cc_address_duplicate_found:
        network_analysis_error_md_update = gr.update(value="<span style='color: red; font-weight: bold;'>CC地址规划错误</span>", visible=True)
    else:
        network_analysis_error_md_update = gr.update(value="", visible=False) # 如果没有错误，则隐藏
    ### 结束新增

    average_peer_score = _process_peer_review_scores(
        [score1_value, score2_value, score3_value, score4_value, score5_value])

    radar_attributes, radar_scores = _calculate_radar_data(error_sections_with_counts, average_peer_score)

    analysis_report_str = _generate_analysis_report(error_sections_with_counts, average_peer_score)

    detailed_errors_md_string = _format_detailed_errors_markdown(detailed_errors, error_sections_with_counts)

    check_result_md_output_update = gr.update(value=check_message_string)
    analysis_output_md_update = gr.update(value=analysis_report_str)
    detailed_errors_output_update = gr.update(value=detailed_errors_md_string)

    single_plot_image_update = gr.update(value=None, visible=False)
    if radar_attributes and radar_scores and len(radar_attributes) >= 3 and len(radar_attributes) == len(radar_scores):
        try:
            fig, ax = plot_attribute_radar(
                character_name=student_name, attributes=radar_attributes, values=radar_scores,
                max_value=100, color='dodgerblue'
            )
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                fig.savefig(tmpfile.name)
                plot_path = tmpfile.name
            plt.close(fig)
            single_student_radar_display_update = gr.update(value=plot_path, visible=True,
                                                            label=f"{student_name} 本次能力雷达图")
        except Exception as e:
            print(f"Error plotting single radar chart for {student_name}: {e}")
            single_student_radar_display_update = gr.update(value=None, visible=False,
                                                            label=f"{student_name} 本次能力雷达图生成失败")
            analysis_output_md_update.value += f"\n\n**注意:** 本次雷达图生成失败，原因：{e}"
    else:
        single_student_radar_display_update = gr.update(value=None, visible=False,
                                                        label=f"{student_name} 本次能力雷达图生成失败")
        analysis_output_md_update.value += "\n\n**注意:** 本次雷达图因数据不足或计算错误未能生成。"

    study_route_plot_path = None
    try:
        fig_mindmap, ax_mindmap = plot_study_route_mindmap(student_name, detailed_errors)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile_mindmap:
            fig_mindmap.savefig(tmpfile_mindmap.name, bbox_inches='tight', dpi=150)
            study_route_plot_path = tmpfile_mindmap.name
        plt.close(fig_mindmap)
        # 确保 study_route_mindmap_display_update 被正确设置为可见
        study_route_mindmap_display_update = gr.update(value=study_route_plot_path, visible=True)
    except Exception as e:
        print(f"Error generating study route mindmap for {student_name}: {e}")
        study_route_mindmap_display_update = gr.update(value=None, visible=False)

    if radar_attributes and radar_scores and len(radar_attributes) >= 3 and len(radar_attributes) == len(radar_scores):
        if student_name not in STUDENT_DATA:
            STUDENT_DATA[student_name] = []
        STUDENT_DATA[student_name].append({'scores': radar_scores, 'attributes': radar_attributes})
        STUDENT_DATA[student_name] = STUDENT_DATA[student_name][-MAX_SUBMISSIONS_HISTORY:]
        print(
            f"Stored data for student: {student_name}. Total submissions for {student_name}: {len(STUDENT_DATA[student_name])}")
    else:
        print(
            f"Warning: Could not store data for student {student_name}. Radar data calculation failed or is insufficient.")

    updated_student_list = list(STUDENT_DATA.keys())
    student_list_choices_update = gr.update(choices=updated_student_list,
                                            value=student_name if student_name in updated_student_list else None,
                                            interactive=True)
    overall_radar_visibility_update = gr.update(visible=len(STUDENT_DATA) > 1, interactive=True)
    current_student_submissions = STUDENT_DATA.get(student_name, [])
    growth_radar_visibility_update = gr.update(visible=(len(current_student_submissions) > 1), interactive=True)

    comparison_radar_display_update = gr.update(value=None, visible=False)
    selected_student_info_md_update = gr.update(
        value="请从下拉列表中选择一个学生查看能力图谱，或点击按钮查看总体能力对比图。")

    final_eval_student_name_display_update = gr.update(value=student_name)

    return (download_file_output_update, check_result_md_output_update, analysis_output_md_update,
            single_student_radar_display_update, detailed_errors_output_update,
            study_route_mindmap_display_update, # 确保 study_route_mindmap_display 在返回列表中
            student_list_choices_update, overall_radar_visibility_update, growth_radar_visibility_update,
            selected_student_info_md_update, comparison_radar_display_update,
            final_eval_student_name_display_update,
            network_analysis_error_md_update) # 更新返回


def view_student_radar(selected_student_name):
    default_image_update = gr.update(value=None, visible=False)
    default_markdown_update = gr.update(value="请从下拉列表中选择一个学生查看能力图谱。")
    growth_button_update = gr.update(visible=False, interactive=True)
    final_eval_student_name_display_update = gr.update(value="")

    if selected_student_name and selected_student_name in STUDENT_DATA:
        student_submissions = STUDENT_DATA[selected_student_name]
        if not student_submissions:
            return default_image_update, default_markdown_update, growth_button_update, final_eval_student_name_display_update

        latest_submission = student_submissions[-1]
        scores = latest_submission.get('scores')
        attributes = latest_submission.get('attributes')

        current_growth_button_visible = len(student_submissions) > 1
        growth_button_update = gr.update(visible=current_growth_button_visible, interactive=True)
        final_eval_student_name_display_update = gr.update(value=selected_student_name)

        if attributes and scores and len(attributes) == len(scores) and len(attributes) >= 3:
            try:
                fig, ax = plot_attribute_radar(
                    character_name=selected_student_name, attributes=attributes, values=scores,
                    max_value=100, color='dodgerblue'
                )
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                    fig.savefig(tmpfile.name)
                    plot_path = tmpfile.name
                plt.close(fig)
                return gr.update(value=plot_path, visible=True,
                                 label=f"{selected_student_name} 最新能力雷达图"), gr.update(
                    value=""), growth_button_update, final_eval_student_name_display_update
            except Exception as e:
                print(f"Error plotting radar for student {selected_student_name}: {e}")
                return default_image_update, gr.update(
                    value=f"为学生 {selected_student_name} 生成雷达图失败: {e}"), growth_button_update, final_eval_student_name_display_update
        else:
            return default_image_update, gr.update(
                value=f"学生 {selected_student_name} 的能力数据不完整或格式错误，无法绘制雷达图。"), growth_button_update, final_eval_student_name_display_update
    else:
        return default_image_update, default_markdown_update, growth_button_update, final_eval_student_name_display_update


def view_student_growth_radar(selected_student_name):
    default_image_update = gr.update(value=None, visible=False)
    default_markdown_update = gr.update(value="需要至少两次提交数据才能绘制成长情况对比图。")

    if selected_student_name and selected_student_name in STUDENT_DATA:
        student_submissions = STUDENT_DATA[selected_student_name]

        if len(student_submissions) < 2:
            return default_image_update, default_markdown_update

        first_attributes = student_submissions[0]['attributes']
        if len(first_attributes) < 3:
            return default_image_update, gr.update(
                value=f"学生 {selected_student_name} 的能力维度少于3个，无法绘制雷达图。")

        valid_submissions = [
            s for s in student_submissions
            if s.get('attributes') == first_attributes and
               s.get('scores') is not None and
               len(s['scores']) == len(first_attributes)
        ]

        if len(valid_submissions) < 2:
            return default_image_update, default_markdown_update

        try:
            fig, ax = plot_history_radar(
                student_name=selected_student_name, submissions=valid_submissions, max_value=100
            )
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                fig.savefig(tmpfile.name)
                plot_path = tmpfile.name
            plt.close(fig)

            return gr.update(value=plot_path, visible=True, label=f"{selected_student_name} 能力成长情况"), gr.update(
                value="")
        except Exception as e:
            print(f"Error plotting growth radar for {selected_student_name}: {e}")
            return default_image_update, gr.update(value=f"生成学生 {selected_student_name} 的成长图失败: {e}")
    else:
        return default_image_update, default_markdown_update


def view_overall_radar():
    default_image_update = gr.update(value=None, visible=False)
    default_markdown_update = gr.update(value="需要至少两位学生的数据完整且一致，才能绘制总体能力对比图。")
    growth_button_update_local = gr.update(visible=False, interactive=True)

    students_to_plot = []
    common_attributes = None

    if STUDENT_DATA:
        student_names_with_data = [name for name, submissions in STUDENT_DATA.items() if submissions]
        if student_names_with_data:
            first_student_name = student_names_with_data[0]
            first_student_history = STUDENT_DATA.get(first_student_name)
            if first_student_history:
                first_student_info = first_student_history[-1]
                common_attributes = first_student_info.get('attributes')

        if common_attributes and len(common_attributes) >= 3:
            num_attributes = len(common_attributes)
            for student_name, student_submissions in STUDENT_DATA.items():
                if student_submissions:
                    latest_submission = student_submissions[-1]
                    scores = latest_submission.get('scores')
                    attributes = latest_submission.get('attributes')
                    if scores is not None and attributes == common_attributes and len(scores) == num_attributes:
                        students_to_plot.append((student_name, scores))
                    else:
                        print(
                            f"Warning: Data mismatch or missing for student {student_name}. Skipping in overall view.")

    if len(students_to_plot) < 2:
        return default_image_update, default_markdown_update, growth_button_update_local

    try:
        fig_compare, ax_compare = plot_comparison_radar(students_to_plot, common_attributes, max_value=100)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            fig_compare.savefig(tmpfile.name)
            plot_path = tmpfile.name
        plt.close(fig_compare)

        return gr.update(value=plot_path, visible=True, label="总体能力对比雷达图"), gr.update(
            value=""), growth_button_update_local

    except Exception as e:
        print(f"Error plotting overall radar chart: {e}")
        return default_image_update, gr.update(
            value=f"生成总体能力对比图失败: {e}"), growth_button_update_local


def submit_final_evaluation(
        student_name_value,
        s_influence, s_coop, s_comm,
        s_prof, s_innov, s_potential
):
    final_eval_radar_output_update = gr.update(value=None, visible=False)
    final_eval_message_update = gr.update(value="")

    student_name = student_name_value.strip()
    if not student_name:
        return final_eval_radar_output_update, gr.update(value="错误：请先在左侧输入或选择学生姓名！")

    if student_name not in STUDENT_DATA or not STUDENT_DATA[student_name]:
        return final_eval_radar_output_update, gr.update(
            value=f"错误：学生 '{student_name}' 没有提交记录，无法获取首次提交成绩。")

    first_submission = STUDENT_DATA[student_name][0]
    first_submission_scores = first_submission.get('scores', [])
    first_submission_avg_score = 0
    if first_submission_scores:
        first_submission_avg_score = np.mean(first_submission_scores)
    else:
        final_eval_message_update = gr.update(
            value=f"注意：学生 '{student_name}' 的首次提交没有有效分数，首次提交平均分将设为0。",
            visible=True)
        print(f"Warning: Student '{student_name}' first submission has no valid scores.")

    attributes = ["影响力", "组内合作能力", "沟通能力", "专业能力", "创新能力", "发展潜力", "首次提交平均分"]
    raw_scores = [s_influence, s_coop, s_comm, s_prof, s_innov, s_potential]
    final_scores = []

    for i, score_val in enumerate(raw_scores):
        if score_val is None:
            final_scores.append(0)
            final_eval_message_update.value += f"\n警告：'{attributes[i]}' 未打分，已设为0分。"
        else:
            final_scores.append(max(0, min(100, float(score_val))))

    final_scores.append(max(0, min(100, float(first_submission_avg_score))))

    if len(final_scores) != len(attributes) or len(attributes) < 3:
        return final_eval_radar_output_update, gr.update(value="错误：雷达图数据不完整或维度不足。")

    try:
        fig, ax = plot_attribute_radar(
            character_name=f"{student_name} 最终评价",
            attributes=attributes,
            values=final_scores,
            max_value=100,
            color='purple',
            title=f"{student_name} 最终综合能力评价"
        )
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            fig.savefig(tmpfile.name)
            plot_path = tmpfile.name
        plt.close(fig)

        final_eval_radar_output_update = gr.update(value=plot_path, visible=True)
        final_eval_message_update = gr.update(value=f"已成功为学生 '{student_name}' 生成最终评价雷达图。", visible=True)

    except Exception as e:
        print(f"Error plotting final evaluation radar chart for {student_name}: {e}")
        final_eval_radar_output_update = gr.update(value=None, visible=False)
        final_eval_message_update = gr.update(value=f"生成最终评价雷达图失败：{e}", visible=True)

    return final_eval_radar_output_update, final_eval_message_update


custom_css = """
/* Style for the home page content wrapper to center its children */
#home-page-wrapper {
    display: flex;
    flex-direction: column;
    justify-content: center; /* Center content vertically */
    align-items: center; /* Center content horizontally */
    min-height: 500px; /* Ensure enough height for vertical centering effect */
    width: 100%; /* Take full width of its parent tab */
    box-sizing: border-box; /* Include padding in element's total width and height */
    padding: 20px;
}

/* Style for the start task button itself */
#start-task-button button {
    padding: 20px 40px; /* Increase padding for a much larger button */
    font-size: 3.6em !important; /* Larger text inside button */
    font-weight: bold; /* Make button text bold */
    min-width: 300px; /* Ensure a generous minimum width */
    height: auto; /* Allow height to adjust with padding/font-size */
    border-radius: 10px; /* Rounded corners */
    box-shadow: 0 4px 8px rgba(0,0,0,0.2); /* Subtle shadow */
    transition: all 0.3s ease; /* Smooth transition for hover effects */
    margin-top: 30px; /* Add some space above the button */
}

/* Hover effect for the start task button */
#start-task-button button:hover {
    background-color: #1a73e8; /* Slightly darker blue on hover */
    box-shadow: 0 6px 12px rgba(0,0,0,0.3); /* More pronounced shadow on hover */
    transform: translateY(-2px); /* Slight lift effect */
}

/* Style for the main home page texts */
#home-page-wrapper h1 {
    font-size: 6em !important; /* Very large title */
    color: #3F51B5; /* Deep blue color */
    margin-bottom: 20px;
    text-align: center;
}

#home-page-wrapper p {
    font-size: 3em !important; /* Larger paragraph text */
    color: #555;
    margin-bottom: 10px;
    text-align: center;
}

/* New: Style for the "信道规划模拟" button */
#channel-planning-button button {
    padding: 15px 30px; /* Large size */
    font-size: 1.2em !important; /* Larger text */
    font-weight: bold;
    min-width: 250px; /* Minimum width */
    height: auto;
    border-radius: 8px;
    box-shadow: 0 3px 6px rgba(0,0,0,0.15);
    transition: all 0.3s ease;
    background-color: #4CAF50; /* Green background, can choose other colors */
    color: white; /* White text */
    border: none;
    margin-bottom: 20px; /* Space below the button */
}

#channel-planning-button button:hover {
    background-color: #45a049; /* Darker green on hover */
    box-shadow: 0 5px 10px rgba(0,0,0,0.25);
    transform: translateY(-1px);
}

/* Increasing font size for the content within specific output markdown tabs */
/* Targets paragraphs, list items, and headings (h3, h4) within elements that have 'output-text' class */
.output-text p,
.output-text li,
.output-text h3,
.output-text h4 {
    font-size: 2.6em !important; /* Increased from 1.15em for better visibility */
    line-height: 1.7; /* Slightly more line spacing for better readability */
}
/* Specific adjustment for pre-formatted text or code blocks often used in detailed errors */
.output-text pre,
.output-text code {
    font-size: 1.2em !important; /* Increased from 1.05em but still slightly smaller than main text */
    line-height: 1.5;
    white-space: pre-wrap; /* Ensure long lines wrap */
    word-wrap: break-word; /* Break long words */
}

/* Ensure the main content tabs have some minimum height to prevent squishing */
.gradio-tab-item {
    min-height: 650px; /* Increased from 600px */
}

/* Style for error messages */
.error-message {
    color: red;
    font-weight: bold;
    margin-top: 5px; /* Space above the error message */
    text-align: center; /* Center the message if needed */
    font-size: 2.2em; /* Slightly larger text for errors */
}



/* General text within paper_tab (paragraphs, markdown text) */
#paper_tab p,
#paper_tab span,
#paper_tab label,
#paper_tab h3,
#paper_tab h4,
#paper_tab .gr-html, /* For generic HTML output (like instructions) */
#paper_tab .gr-block-label { /* Labels for blocks like Dataframe */
    font-size: 2.4em !important; /* Increase most text content */
    line-height: 1.6; /* Improve readability */
}

/* Text in input fields (Textbox, Number) */
#paper_tab .gr-textbox input,
#paper_tab .gr-number input,
#paper_tab .gr-dropdown select { /* For dropdown value */
    font-size: 2.4em !important;
    padding: 8px 10px !important; /* Adjust padding for better appearance with larger text */
}

/* Table headers and data cells */
#paper_tab .gr-dataframe table th,
#paper_tab .gr-dataframe table td {
    font-size: 2.3em !important; /* For table content, slightly smaller than main text for compactness */
    padding: 8px 6px !important; /* Adjust cell padding for larger text */
    line-height: 1.4;
}

/* Ensure dataframe cells don't overflow with larger text */
#paper_tab .gr-dataframe {
    overflow-x: auto; /* Allow horizontal scroll if table content is too wide */
}

/* --- 结束新增：答卷填写与分析页面字体放大 --- */

/* --- 新增：随堂测试页面字体放大 --- */
#quiz_tab p,
#quiz_tab label,
#quiz_tab h3,
#quiz_tab h4,
#quiz_tab .gr-html {
    font-size: 2.5em !important; /* For questions and labels */
    line-height: 1.6;
}

#quiz_tab .gr-radio label span { /* Specific for radio button text */
    font-size: 2.4em !important;
}

#quiz_tab .output-text p,
#quiz_tab .output-text li,
#quiz_tab .output-text h3,
#quiz_tab .output-text h4 {
    font-size: 2.6em !important; /* Make quiz results slightly larger */
}
/* --- 结束新增：随堂测试页面字体放大 --- */

/* --- 新增：最终评价页面字体放大 --- */
#final_evaluation_tab p,
#final_evaluation_tab label,
#final_evaluation_tab h3,
#final_evaluation_tab h4 {
    font-size: 2.4em !important;
    line-height: 1.6;
}

#final_evaluation_tab .gr-number input {
    font-size: 2.4em !important;
    padding: 8px 10px !important;
}
/* --- 结束新增：最终评价页面字体放大 --- */

"""

with gr.Blocks(css=custom_css) as demo:
    with gr.Tabs() as overall_tabs:
        with gr.Tab("主页", id="home_tab"):
            with gr.Column(elem_id="home-page-wrapper"):
                gr.Markdown("<h1>大型任务</h1>")
                gr.Markdown("<p><strong>时间：</strong>2023年10月27日</p>")
                gr.Markdown(
                    "<p><strong>任务：：</strong>完成网络组网参数配置与分析</p>")

                with gr.Row():
                    gr.Column(scale=1)
                    start_task_button = gr.Button("任务开始", variant="primary", elem_id="start-task-button")
                    gr.Column(scale=1)

        with gr.Tab("任务内容", id="paper_app_tab"):
            gr.Markdown("<h2 style='text-align: center;'>任务书</h2>")
            with gr.Row():
                student_name_input = gr.Textbox(label="请输入您的姓名：", placeholder="例如：张三", scale=2)
                quiz_tab_selector_button = gr.Button("随堂测试", scale=1, variant="secondary")
            gr.Markdown("---")

            with gr.Tabs() as main_tabs:
                with gr.Tab("答卷填写与分析", id="paper_tab"):
                    gr.Markdown("请注意：请仅填写空白处的内容。**以下部分 (1.xx参数, 2.Xxx站配置参数) 不计入成绩。**",
                                show_label=False)
                    gr.Markdown(
                        f"提交后将生成答卷结果TXT文件，并与内置标准答案/逻辑进行比对，显示错误个数，并给出能力分析报告及雷达图。",
                        show_label=False)
                    gr.Markdown("---")
                    gr.Markdown("### 1.xx参数")
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Row():
                                subnet_id_input = gr.Textbox(label="子网编号", placeholder="在此填写...",
                                                             interactive=True)
                            with gr.Row():
                                network_name_input = gr.Textbox(label="网络名称", placeholder="在此填写...",
                                                                interactive=True)
                        with gr.Column(scale=3):
                            pass

                    gr.Markdown("### 2.Xxx站配置参数")
                    station_config_table = gr.Dataframe(value=station_config_data, headers=station_config_headers,
                                                        interactive=True,
                                                        show_label=False, wrap=True)
                    gr.Markdown("---")

                    gr.Markdown("### 3.信道段参数")
                    channel_type_dropdown = gr.Dropdown(
                        label=_CHANNEL_TYPE_LABEL,
                        choices=["aa", "uu"],
                        value="aa",
                        interactive=True,
                        scale=1
                    )
                    channel_segment_table = gr.Dataframe(value=channel_segment_data, headers=channel_segment_headers,
                                                         interactive=True,
                                                         show_label=False, wrap=True)
                    gr.Markdown("---")

                    gr.Markdown("### 4.控制信道参数")
                    gr.Markdown("说明：请根据说明完成后续内容")
                    # 使用新的表头和数据
                    channel_suite_table = gr.Dataframe(value=channel_suite_data, headers=channel_suite_headers,
                                                       interactive=True,
                                                       show_label=False, wrap=True,
                                                       # 确保列数固定，防止用户添加/删除列
                                                       col_count=(len(channel_suite_headers), "fixed"))
                    gr.Markdown("---")

                    gr.Markdown("## ——————————第二模块——————————")

                    gr.Markdown("### 1.通信终端参数分析")
                    gr.Markdown("说明：**CC地址** 列中的内容不可重复，如有重复，重复的单元格将被标记为错误。",
                                show_label=False)
                    network_analysis_table = gr.Dataframe(value=network_analysis_data, headers=network_analysis_headers,
                                                          interactive=True, show_label=False, wrap=True)
                    ### 新增：用于显示CC地址重复错误的Markdown组件
                    network_analysis_error_message = gr.Markdown("", visible=False, elem_classes=["error-message"])
                    ### 结束新增
                    gr.Markdown("---")


                    gr.Markdown("### 2.虚拟子网参数")
                    gr.Markdown(
                        "说明：请根据速率选择列表中的速率，填写相应的带宽和频率范围。下行和上行频率范围不允许重叠。")
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Row():
                                local_cc_address_input = gr.Textbox(label="成员CU地址（用顿号隔开）",
                                                                    placeholder="在此填写...",
                                                                    interactive=True)
                    virtual_subnet_table = gr.Dataframe(value=virtual_subnet_data, headers=virtual_subnet_headers,
                                                        interactive=True,
                                                        show_label=False, wrap=True,
                                                        col_count=(len(virtual_subnet_headers), "fixed")
                                                        )
                    gr.Markdown("---")

                    gr.Markdown("### 3.点对点通信参数")
                    gr.Markdown("说明：请根据说明完成后续内容")
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Row():
                                local_cc_address_input = gr.Textbox(label="本端CC地址", placeholder="在此填写...",
                                                                    interactive=True)
                            with gr.Row():
                                remote_xx_address_input = gr.Textbox(label="对端XX地址", placeholder="在此填写...",
                                                                     interactive=True)
                        with gr.Column(scale=3):
                            pass

                    p2p_table = gr.Dataframe(value=p2p_data, headers=p2p_headers, interactive=True, show_label=False,
                                             wrap=True)
                    gr.Markdown("---")

                    gr.Markdown("### 组内评价")
                    with gr.Row():
                        gr.Markdown("请为组内成员（或多个方面）打分 (0-100，可留空):")
                    with gr.Row(equal_height=True):
                        score_input_1 = gr.Number(label="分数1", minimum=0, maximum=100, step=1, scale=1)
                        score_input_2 = gr.Number(label="分数2", minimum=0, maximum=100, step=1, scale=1)
                        score_input_3 = gr.Number(label="分数3", minimum=0, maximum=100, step=1, scale=1)
                        score_input_4 = gr.Number(label="分数4", minimum=0, maximum=100, step=1, scale=1)
                        score_input_5 = gr.Number(label="分数5", minimum=0, maximum=100, step=1, scale=1)
                    gr.Markdown("---")

                    channel_planning_button = gr.Button(
                        "信道规划模拟",
                        variant="secondary",
                        link="/static/slide.html",
                        elem_id="channel-planning-button"
                    )
                    gr.Markdown("---")

                    submit_button = gr.Button("提交并检查", variant="primary")

                    with gr.Row():
                        with gr.Column(scale=2):
                            with gr.Tabs() as results_tabs:
                                with gr.Tab("答卷填写与分析 (汇总)"):
                                    check_result_output_md = gr.Markdown("点击提交按钮进行检查...",
                                                                         elem_classes=["output-text"])
                                with gr.Tab("详细错误列表"):
                                    detailed_errors_output_md = gr.Markdown("等待检查结果...",
                                                                            elem_classes=["output-text"])
                                with gr.Tab("能力分析报告"):
                                    analysis_output_md = gr.Markdown("等待检查结果...", elem_classes=["output-text"])
                                with gr.Tab("学习路线"): # 取消注释以显示学习路线思维导图
                                    study_route_mindmap_display = gr.Image(label=None, show_label=False,
                                                                           type="filepath",
                                                                           interactive=False, visible=False)
                            download_file_output = gr.File(label="下载答卷结果",
                                                           visible=False)

                        with gr.Column(scale=1):
                            gr.Markdown("### 本次能力图谱")
                            single_student_radar_display = gr.Image(label=None, show_label=False, type="filepath",
                                                                    interactive=False,
                                                                    visible=False)

                            gr.Markdown("---")

                            gr.Markdown("### 已保存学生能力分析")
                            with gr.Row():
                                student_list_dropdown = gr.Dropdown(label="选择学生查看能力图", choices=[], scale=2,
                                                                    interactive=True)
                                overall_radar_button = gr.Button("查看总体能力对比图", scale=1, visible=False,
                                                                 interactive=True)
                            growth_radar_button = gr.Button("查看成长情况", visible=False, interactive=True)

                            selected_student_info_md = gr.Markdown(
                                "请从下拉列表中选择一个学生查看能力图谱，或点击按钮查看总体能力对比图。")
                            comparison_radar_display = gr.Image(label=None, show_label=False, type="filepath",
                                                                interactive=False,
                                                                visible=False)

                with gr.Tab("随堂测试", id="quiz_tab"):
                    gr.Markdown("## 随堂测试")
                    gr.Markdown("请完成以下5道选择题：")

                    quiz_inputs = []
                    for i, q_data in enumerate(QUIZ_QUESTIONS):
                        gr.Markdown(f"### {q_data['question']}")
                        radio = gr.Radio(choices=q_data['options'], label=f"请选择Q{i + 1}的答案", type="value",
                                         interactive=True)
                        quiz_inputs.append(radio)

                    submit_quiz_button = gr.Button("提交测试", variant="primary")

                    with gr.Column():
                        quiz_result_output_md = gr.Markdown("点击提交测试按钮查看结果...",
                                                            visible=True, elem_classes=["output-text"])
                        quiz_stats_output_md = gr.Markdown(display_quiz_stats(), visible=True,
                                                           elem_classes=["output-text"])

        with gr.Tab("最终评价", id="final_evaluation_tab"):
            gr.Markdown("## 最终评价")
            final_eval_student_name_display = gr.Textbox(label="当前评价学生", interactive=False,
                                                         placeholder="请在'任务内容'页面提交或选择学生")
            gr.Markdown("---")

            gr.Markdown("### 组长打分 (0-100)")
            with gr.Row():
                leader_score_influence = gr.Number(label="影响力", minimum=0, maximum=100, step=1, scale=1)
                leader_score_coop = gr.Number(label="组内合作能力", minimum=0, maximum=100, step=1, scale=1)
                leader_score_comm = gr.Number(label="沟通能力", minimum=0, maximum=100, step=1, scale=1)

            gr.Markdown("### 教师打分 (0-100)")
            with gr.Row():
                teacher_score_prof = gr.Number(label="专业能力", minimum=0, maximum=100, step=1, scale=1)
                teacher_score_innov = gr.Number(label="创新能力", minimum=0, maximum=100, step=1, scale=1)
                teacher_score_potential = gr.Number(label="发展潜力", minimum=0, maximum=100, step=1, scale=1)

            submit_final_evaluation_button = gr.Button("提交最终评价", variant="primary")

            final_eval_radar_output = gr.Image(label=None, show_label=False, type="filepath", interactive=False,
                                               visible=False)
            final_eval_message = gr.Markdown("")

    start_task_button.click(
        lambda: gr.update(selected="paper_app_tab"),
        outputs=[overall_tabs]
    )

    submit_button.click(
        fn=process_submission,
        inputs=[
            student_name_input,
            subnet_id_input, network_name_input, station_config_table, channel_segment_table,
            channel_suite_table, network_analysis_table, local_cc_address_input,
            remote_xx_address_input, p2p_table, virtual_subnet_table,
            channel_type_dropdown,
            score_input_1, score_input_2, score_input_3, score_input_4, score_input_5
        ],
        outputs=[
            download_file_output,
            check_result_output_md,
            analysis_output_md,
            single_student_radar_display,
            detailed_errors_output_md,
            study_route_mindmap_display, # 确保学习路线图被正确输出
            student_list_dropdown,
            overall_radar_button,
            growth_radar_button,
            selected_student_info_md,
            comparison_radar_display,
            final_eval_student_name_display,
            network_analysis_error_message
        ]
    ).then(
        fn=view_student_radar,
        inputs=[student_list_dropdown],
        outputs=[comparison_radar_display, selected_student_info_md, growth_radar_button,
                 final_eval_student_name_display]
    )

    student_list_dropdown.change(
        fn=view_student_radar,
        inputs=[student_list_dropdown],
        outputs=[comparison_radar_display, selected_student_info_md, growth_radar_button,
                 final_eval_student_name_display]
    )

    overall_radar_button.click(
        fn=view_overall_radar,
        inputs=[],
        outputs=[comparison_radar_display, selected_student_info_md, growth_radar_button]
    )

    growth_radar_button.click(
        fn=view_student_growth_radar,
        inputs=[student_list_dropdown],
        outputs=[comparison_radar_display, selected_student_info_md]
    )

    submit_quiz_button.click(
        fn=submit_quiz,
        inputs=quiz_inputs,
        outputs=[quiz_result_output_md, quiz_stats_output_md]
    )

    quiz_tab_selector_button.click(
        lambda: gr.update(selected="quiz_tab"),
        outputs=[main_tabs]
    )

    submit_final_evaluation_button.click(
        fn=submit_final_evaluation,
        inputs=[
            final_eval_student_name_display,
            leader_score_influence,
            leader_score_coop,
            leader_score_comm,
            teacher_score_prof,
            teacher_score_innov,
            teacher_score_potential
        ],
        outputs=[final_eval_radar_output, final_eval_message]
    )

if __name__ == "__main__":
    print(f"Starting Gradio app...")
    try:
        demo.launch(debug=True, share=False)
    except Exception as e:
        print(f"Error launching Gradio app: {e}")