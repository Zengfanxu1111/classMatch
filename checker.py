import io
import sys
import os
import pandas as pd
from collections import defaultdict

# --- 静态标签定义 (用于生成输出字符串，确保与主文件界面上的标签一致) ---
_SUBNET_ID_LABEL = "子网编号："
_NETWORK_NAME_LABEL = "网络名称："
_LOCAL_CC_ADDRESS_LABEL = "本端CC地址:"
_REMOTE_XX_ADDRESS_LABEL = "对端XX地址："
_CHANNEL_TYPE_LABEL = "信道类型选择："  # 新增标签

# --- 静态的正确答案定义 (注意: 这些定义本身不再用于计分，但标签和结构用于界面和文件捕获) ---
# 移除了 (1) xx参数 和 (2) Xxx站配置参数 的正确答案定义，因为它们不再计入成绩。

# (3) 信道段参数 (NOTE: Specific values are now logic-dependent, not fixed here)
_CHANNEL_SEGMENT_HEADERS = ["卫星名称", "下行起始频率（khz）", "下行终止频率（khz）", "上行起始频率（khz）",
                            "上行终止频率（khz）"]
_CHANNEL_SEGMENT_FILLABLE_COLS_INDICES = [1, 2, 3, 4]  # Assuming 卫星名称是预填的，用户填写频率
_CORRECT_CHANNEL_TYPE = "uu"  # 假设正确的信道类型是 "uu"

# (4) 信道套参数 - NOTE: 正确答案定义已不再是硬编码，而是通过逻辑动态计算
# _CORRECT_CHANNEL_SUITE_VALUES 已经不再使用，将被移除
# 修改此处的表头以匹配新的3x5表格样式
_CHANNEL_SUITE_HEADERS = ["名称", "速率kbps", "带宽khz", "上行中心频点khz", "下行中心频点khz"]
# _CHANNEL_SUITE_FILLABLE_COLS_INDICES 已经不再使用，将被移除

# 1.组网参数分析 - 正确答案定义已不再用于此部分，因为检查逻辑改变为检查重复
# 保留 headers 以便报告使用
_NETWORK_ANALYSIS_HEADERS = ["用户单位", "站型", "站地址", "CC地址", "电话号码", "设备序列号"]
# _NETWORK_ANALYSIS_FILLABLE_COLS_INDICES = [1, 2, 3, 4] # 不再需要这个用于计分

# 2.点对点通信参数
# IMPORTANT: Correct answers for specific values are NOT defined here, as they are no longer checked for exact match.
# Only KBP and frequency relationship rules apply.
# _CORRECT_LOCAL_CC_ADDRESS and _CORRECT_REMOTE_XX_ADDRESS are KEPT as placeholders for interface labels.
_CORRECT_LOCAL_CC_ADDRESS = "192.168.1.100"  # Placeholder, no longer checked for exact match
_CORRECT_REMOTE_XX_ADDRESS = "10.0.0.1"  # Placeholder, no longer checked for exact match

_P2P_HEADERS = ["名称", "速率kbps", "带宽（khz）", "下行起始频点（khz）", "下行终止频点（khz）", "上行起始频点（khz）",
                "上行终止频点（khz）"]
_P2P_FILLABLE_COLS_INDICES = [1, 2, 3, 4, 5,
                              6]  # RE-ENABLED: Used for general structure checks, not exact content matching.
_P2P_RATE_COL_INDEX = 1
_P2P_BANDWIDTH_COL_INDEX = 2
_P2P_DOWNLINK_START_COL_INDEX = 3
_P2P_UPLINK_END_COL_INDEX = 6

# 3.虚拟子网参数
# 移除 _CORRECT_VIRTUAL_SUBNET_VALUES
_VIRTUAL_SUBNET_HEADERS = ["名称", "带宽（khz）", "下行起始频率（khz）", "下行终止频率（khz）", "上行起始频率（khz）",
                           "上行终止频率（khz）"]
# 移除 _VIRTUAL_SUBNET_FILLABLE_COLS_INDICES

# --- Check Type Constants ---
_CHECK_TYPE_TEXTBOX_GROUP = "textbox_group" # Not used in current logic
_CHECK_TYPE_DATAFRAME = "dataframe" # Not used in current logic
_CHECK_TYPE_CHANNEL_FREQUENCY_LOGIC = "channel_frequency_logic"
_CHECK_TYPE_TEXTBOX_AND_DATAFRAME = "textbox_and_dataframe"
_CHECK_TYPE_DATAFRAME_COLUMN_DUPLICATE = "dataframe_column_duplicate_check"
_CHECK_TYPE_CHANNEL_SUITE_LOGIC = "channel_suite_logic"
_CHECK_TYPE_VIRTUAL_SUBNET_LOGIC = "virtual_subnet_logic"  # 新增：虚拟子网的自定义逻辑检查类型

# --- 用于比较的逻辑段落配置 ---
_COMPARISON_CONFIG = {
    "（3）信道段参数": {
        "check_type": _CHECK_TYPE_CHANNEL_FREQUENCY_LOGIC,
        "report_headers": _CHANNEL_SEGMENT_HEADERS,
        "dropdown_label": _CHANNEL_TYPE_LABEL,
        "correct_dropdown_value": _CORRECT_CHANNEL_TYPE,  # 即使不校验，这个值也会在后续逻辑中作为默认或参考
        "params": ["channel_segment_value", "channel_type_value"]
    },
    "（4）信道套参数": {
        "check_type": _CHECK_TYPE_CHANNEL_SUITE_LOGIC,
        "report_headers": _CHANNEL_SUITE_HEADERS, # 引用更新后的表头
        "params": ["channel_suite_value", "channel_segment_value"]
    },
    "1.组网参数分析": {
        "check_type": _CHECK_TYPE_DATAFRAME_COLUMN_DUPLICATE,
        "report_headers": _NETWORK_ANALYSIS_HEADERS,
        "param": "network_analysis_value",
        "column_to_check_index": 3,
        "column_to_check_name": "CC地址"
    },
    "2.点对点通信参数": {
        "check_type": _CHECK_TYPE_TEXTBOX_AND_DATAFRAME,
        "fields": [_LOCAL_CC_ADDRESS_LABEL, _REMOTE_XX_ADDRESS_LABEL],
        "correct_textbox_answers": [_CORRECT_LOCAL_CC_ADDRESS, _CORRECT_REMOTE_XX_ADDRESS], # These are placeholders for labels, not used for exact matching in current check_paper logic.
        "report_headers": _P2P_HEADERS,
        "fillable_cols_indices": _P2P_FILLABLE_COLS_INDICES,
        "params": ["local_cc_address_value", "remote_xx_address_value", "p2p_value"]
    },
    "3.虚拟子网参数": {
        "check_type": _CHECK_TYPE_VIRTUAL_SUBNET_LOGIC,
        "report_headers": _VIRTUAL_SUBNET_HEADERS,
        "params": ["virtual_subnet_value", "virtual_subnet_rate_value"]
    }
}

# --- KBP映射硬编码 ---
_KBP_MAPPING = {
    32: 42,
    64: 84,
    128: 168,
    256: 336,
    512: 671,
    1024: 895,
    2048: 1789,
}


# --- 函数 1: 捕获用户输入并格式化为字符串 (用于下载，功能不变) ---
def capture_paper_data_string(
        subnet_id_value, network_name_value,
        station_config_headers, station_config_value,
        channel_segment_headers, channel_segment_value,
        channel_suite_headers, channel_suite_value,
        network_analysis_headers, network_analysis_value,
        local_cc_address_value, remote_xx_address_value,
        p2p_headers, p2p_value,
        virtual_subnet_headers, virtual_subnet_value,
        channel_type_value
):
    """
    捕获所有用户输入数据，并将其格式化为可读的字符串，用于下载保存。
    """
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    try:
        print("--- 试卷填写结果 ---")

        print(f"\n(1) xx参数")
        print(f"{_SUBNET_ID_LABEL} {subnet_id_value}")
        print(f"{_NETWORK_NAME_LABEL} {network_name_value}")

        print(f"\n(2) Xxx站配置参数:")
        print("Headers:", station_config_headers)
        station_config_list = station_config_value.values.tolist() if isinstance(station_config_value,
                                                                                 pd.DataFrame) else station_config_value
        print("Data:", station_config_list)

        print(f"\n(3) 信道段参数:")
        print("Headers:", channel_segment_headers)
        channel_segment_list = channel_segment_value.values.tolist() if isinstance(channel_segment_value,
                                                                                   pd.DataFrame) else channel_segment_value
        print("Data:", channel_segment_list)
        print(f"{_CHANNEL_TYPE_LABEL} {channel_type_value}")

        print(f"\n(4) 信道套参数:")
        print("Headers:", channel_suite_headers) # 这里会使用更新后的表头
        channel_suite_list = channel_suite_value.values.tolist() if isinstance(channel_suite_value,
                                                                               pd.DataFrame) else channel_suite_value
        print("Data:", channel_suite_list)

        print(f"\n1.组网参数分析:")
        print("Headers:", network_analysis_headers)
        network_analysis_list = network_analysis_value.values.tolist() if isinstance(network_analysis_value,
                                                                                     pd.DataFrame) else network_analysis_value
        print("Data:", network_analysis_list)

        print(f"\n2.点对点通信参数:")
        print(f"{_LOCAL_CC_ADDRESS_LABEL} {local_cc_address_value}")
        print(f"{_REMOTE_XX_ADDRESS_LABEL} {remote_xx_address_value}")
        print("\n点对点通信参数表:")
        p2p_list = p2p_value.values.tolist() if isinstance(p2p_value, pd.DataFrame) else p2p_value
        print("Data:", p2p_list)

        print(f"\n3.虚拟子网参数:")
        print("Headers:", virtual_subnet_headers)
        virtual_subnet_list = virtual_subnet_value.values.tolist() if isinstance(virtual_subnet_value,
                                                                                 pd.DataFrame) else virtual_subnet_value
        print("Data:", virtual_subnet_list)

        print("\n--- 捕获结束 ---")

    finally:
        sys.stdout = old_stdout
    return redirected_output.getvalue()


# --- 辅助函数：检查上行终止频率是否大于下行起始频率 ---
def _check_uplink_downlink_frequency_rule(section_title, user_row_index,
                                          downlink_start_freq_val, uplink_end_freq_val,
                                          downlink_start_col_header, uplink_end_col_header):
    errors = []
    error_count = 0
    try:
        dl_start = float(str(downlink_start_freq_val).strip())
        ul_end = float(str(uplink_end_freq_val).strip())

        if ul_end > dl_start:
            error_count += 1
            errors.append({
                'section_title': section_title,
                'type': 'frequency_logic_error',
                'row': user_row_index,
                'col_header_ul_end': uplink_end_col_header,
                'col_header_dl_start': downlink_start_col_header,
                'user_value_ul_end': f"{ul_end:.2f}",
                'user_value_dl_start': f"{dl_start:.2f}",
                'message': f"上行终止频率 ({ul_end:.2f}khz) 不应大于下行起始频率 ({dl_start:.2f}khz)。"
            })
    except (ValueError, TypeError):
        error_count += 1
        errors.append({
            'section_title': section_title,
            'type': 'data_type_error',
            'row': user_row_index,
            'message': f"频率值 '{downlink_start_freq_val}' 或 '{uplink_end_freq_val}' 应为有效数字，无法进行频点逻辑校验。"
        })
    return error_count, errors


# 检查带宽是否大于等于对应速率的带宽
def _check_bandwidth_vs_rate_rule(section_title, user_row_index, user_rate_val, user_bandwidth_val,
                                  rate_col_header, bandwidth_col_header, kbp_mapping):
    errors = []
    error_count = 0

    try:
        user_rate = int(str(user_rate_val).strip())
        user_bandwidth = int(str(user_bandwidth_val).strip())

        if user_rate not in kbp_mapping:
            error_count += 1
            errors.append({
                'section_title': section_title,
                'type': 'bandwidth_rate_mismatch',
                'row': user_row_index,
                'col_header_rate': rate_col_header,
                'col_header_bandwidth': bandwidth_col_header,
                'user_value_rate': f"{user_rate}",
                'user_value_bandwidth': f"{user_bandwidth}",
                'message': f"速率 '{user_rate}' 在KBP映射中未找到对应带宽。请核对速率值。"
            })
        else:
            required_bandwidth = kbp_mapping[user_rate]
            if user_bandwidth < required_bandwidth:
                error_count += 1
                errors.append({
                    'section_title': section_title,
                    'type': 'bandwidth_rate_mismatch',
                    'row': user_row_index,
                    'col_header_rate': rate_col_header,
                    'col_header_bandwidth': bandwidth_col_header,
                    'user_value_rate': f"{user_rate}",
                    'user_value_bandwidth': f"{user_bandwidth}",
                    'answer_value_required_bandwidth': f"{required_bandwidth}",
                    'message': f"带宽 ({user_bandwidth}khz) 小于速率 {user_rate}kbps 对应的最低要求带宽 ({required_bandwidth}khz)。"
                })
    except (ValueError, TypeError):
        error_count += 1
        errors.append({
            'section_title': section_title,
            'type': 'data_type_error',
            'row': user_row_index,
            'message': f"速率 '{user_rate_val}' 或带宽 '{user_bandwidth_val}' 应为有效数字，无法进行带宽速率校验。"
        })
    except Exception as e:
        error_count += 1
        errors.append({
            'section_title': section_title,
            'type': 'bandwidth_rate_mismatch',
            'row': user_row_index,
            'message': f"带宽与速率对应关系检查时发生内部错误: {e}"
        })
    return error_count, errors


# 新增辅助函数：检查两个频率范围是否重叠
def _check_frequency_overlap_rule(section_title, user_row_index,
                                  dl_start, dl_end, ul_start, ul_end,
                                  dl_start_col_header, dl_end_col_header, ul_start_col_header, ul_end_col_header):
    errors = []
    error_count = 0
    try:
        dl_start_f = float(str(dl_start).strip())
        dl_end_f = float(str(dl_end).strip())
        ul_start_f = float(str(ul_start).strip())
        ul_end_f = float(str(ul_end).strip())

        # 确保频率范围是有效的 (起始 <= 终止)
        if dl_start_f > dl_end_f:
            error_count += 1
            errors.append({
                'section_title': section_title,
                'type': 'frequency_logic_error',
                'row': user_row_index,
                'message': f"下行起始频率({dl_start_f})不能大于下行终止频率({dl_end_f})。"
            })
        if ul_start_f > ul_end_f:
            error_count += 1
            errors.append({
                'section_title': section_title,
                'type': 'frequency_logic_error',
                'row': user_row_index,
                'message': f"上行起始频率({ul_start_f})不能大于上行终止频率({ul_end_f})。"
            })

        # 判断两个区间 [a, b] 和 [c, d] 是否重叠：当且仅当 max(a, c) < min(b, d) 时重叠
        # 这里要检查的是不能重叠，所以如果重叠，就报错。
        if max(dl_start_f, ul_start_f) < min(dl_end_f,
                                             ul_end_f):
            error_count += 1
            errors.append({
                'section_title': section_title,
                'type': 'frequency_logic_error',
                'row': user_row_index,
                'message': f"频率范围重叠：下行频率范围[{dl_start_f:.2f}-{dl_end_f:.2f}]与上行频率范围[{ul_start_f:.2f}-{ul_end_f:.2f}]重叠，不允许。",
                'user_value_dl_start': f"{dl_start_f:.2f}",
                'user_value_dl_end': f"{dl_end_f:.2f}",
                'user_value_ul_start': f"{ul_start_f:.2f}",
                'user_value_ul_end': f"{ul_end_f:.2f}",
                'col_header_dl_start': dl_start_col_header,
                'col_header_dl_end': dl_end_col_header,
                'col_header_ul_start': ul_start_col_header,
                'col_header_ul_end': ul_end_col_header,
            })

    except (ValueError, TypeError):
        error_count += 1
        errors.append({
            'section_title': section_title,
            'type': 'data_type_error',
            'row': user_row_index,
            'message': f"频率值应为数字，无法进行频率重叠校验。"
        })
    return error_count, errors


# --- 函数 2: 对比用户输出与正确答案并计算错误个数及详细错误 ---
def check_paper(
        subnet_id_value, network_name_value,
        station_config_value,
        channel_segment_value, channel_type_value,
        channel_suite_value,
        network_analysis_value,
        local_cc_address_value, remote_xx_address_value, p2p_value,
        virtual_subnet_value,
        virtual_subnet_rate_value
):
    """
    将用户答卷结果直接与内置的正确答案/逻辑进行对比，计算并返回错误个数、错误部分的标题列表，
    以及详细的错误信息列表。
    """
    error_sections_with_counts = []
    error_titles_only = []
    detailed_errors = []

    input_values = {
        "subnet_id_value": subnet_id_value,
        "network_name_value": network_name_value,
        "station_config_value": station_config_value,
        "channel_segment_value": channel_segment_value,
        "channel_type_value": channel_type_value,
        "channel_suite_value": channel_suite_value,
        "network_analysis_value": network_analysis_value,
        "local_cc_address_value": local_cc_address_value,
        "remote_xx_address_value": remote_xx_address_value,
        "p2p_value": p2p_value,
        "virtual_subnet_value": virtual_subnet_value,
        "virtual_subnet_rate_value": virtual_subnet_rate_value
    }

    def _df_to_lol(df_value):
        if isinstance(df_value, pd.DataFrame):
            return df_value.values.tolist()
        return df_value

    for friendly_title, config in _COMPARISON_CONFIG.items():
        current_section_error_count = 0
        current_section_detailed_errors = []
        section_format_error = False

        # NOTE: The _CHECK_TYPE_DATAFRAME block is removed as it's no longer used.
        # All sections now use specific logic checks like _CHECK_TYPE_CHANNEL_FREQUENCY_LOGIC, etc.

        if config["check_type"] == _CHECK_TYPE_DATAFRAME_COLUMN_DUPLICATE:
            user_df_value = _df_to_lol(input_values[config["param"]])
            col_to_check_idx = config["column_to_check_index"]
            col_to_check_name = config["column_to_check_name"]
            report_headers = config["report_headers"]

            if not isinstance(user_df_value, list) or not all(isinstance(row, list) for row in user_df_value):
                section_format_error = True
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': "组网参数分析表格格式错误或无法解析。请确保输入为有效数据。"
                })

            if not section_format_error:
                value_first_row_map = {}
                duplicate_rows_map = defaultdict(list)

                for r, row in enumerate(user_df_value):
                    if col_to_check_idx < len(row):
                        cell_value = str(row[col_to_check_idx]).strip()
                        if cell_value and cell_value != "":
                            # Only add to duplicates if it's not the first occurrence of this value
                            if cell_value in value_first_row_map:
                                duplicate_rows_map[cell_value].append(r)
                            else:
                                value_first_row_map[cell_value] = r
                    else:
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'column_count_mismatch',
                            'row': r + 1,
                            'message': f"第 {r + 1} 行列数不足，缺少CC地址列，无法进行重复性校验。"
                        })

                for value, row_indices in duplicate_rows_map.items():
                    # Each subsequent duplicate for a value adds to the error count
                    current_section_error_count += len(row_indices) # This counts each *additional* occurrence as an error
                    col_header_display = report_headers[col_to_check_idx] if col_to_check_idx < len(
                        report_headers) else f"列 {col_to_check_idx + 1}"

                    for dup_r in row_indices:
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'dataframe_duplicate',
                            'row': dup_r + 1,
                            'col': col_to_check_idx + 1,
                            'col_header': col_header_display,
                            'user_value': value,
                            'message': f"值 '{value}' 在此行重复出现。CC地址列不允许重复。"
                        })

        elif config["check_type"] == _CHECK_TYPE_CHANNEL_FREQUENCY_LOGIC:
            user_df_value = _df_to_lol(input_values[config["params"][0]])
            user_channel_type = str(input_values[config["params"][1]]).strip()
            report_headers = config["report_headers"]
            tolerance = 1e-6

            # # --- Removed: Logic for checking dropdown value directly. It's now used for calculations only. ---
            # correct_dropdown_val = str(config["correct_dropdown_value"]).strip()
            # if user_channel_type != correct_dropdown_val:
            #     current_section_error_count += 1
            #     current_section_detailed_errors.append({
            #         'section_title': friendly_title,
            #         'type': 'dropdown',
            #         'field_label': config["dropdown_label"],
            #         'user_value': user_channel_type,
            #         'answer_value': correct_dropdown_val,
            #         'message': f"信道类型应为 '{correct_dropdown_val}'。"
            #     })
            # # --- End Removed ---

            user_downlink_start = user_downlink_end = user_uplink_start = user_uplink_end = None
            frequencies_parsed = False

            if not isinstance(user_df_value, list) or len(user_df_value) == 0 or not all(
                    isinstance(row, list) for row in user_df_value):
                section_format_error = True
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': "信道段参数表格格式错误或为空。无法解析频率数据。"
                })

            if not section_format_error:
                user_row = user_df_value[0]
                expected_cols = 5

                if len(user_row) < expected_cols:
                    current_section_error_count += (expected_cols - 1) # Satellite name is fixed, so 4 fillable columns
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'column_count_mismatch',
                        'row': 1,
                        'message': f"信道段参数表格第一行列数不足，应至少包含 {expected_cols} 列。",
                        'user_value': str(len(user_row)),
                        'answer_value': f"至少需要 {expected_cols} 列"
                    })
                else:
                    try:
                        user_downlink_start = float(str(user_row[1]).strip())
                        user_downlink_end = float(str(user_row[2]).strip())
                        user_uplink_start = float(str(user_row[3]).strip())
                        user_uplink_end = float(str(user_row[4]).strip())
                        frequencies_parsed = True
                    except (ValueError, TypeError):
                        current_section_error_count += 4 # All four frequency values
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'data_type_error',
                            'message': "频率值应为数字，请检查输入。"
                        })

            if frequencies_parsed:
                if user_channel_type == "uu":
                    downlink_min, downlink_max = 12.25, 12.75
                    uplink_min, uplink_max = 14.0, 14.5
                    offset = 1.75
                elif user_channel_type == "aa":
                    downlink_min, downlink_max = 19.6, 21.2
                    uplink_min, uplink_max = 29.4, 31.0
                    offset = 9.8
                else:
                    # 如果信道类型不是uu或aa，则无法进行后续依赖此类型的频率逻辑检查
                    current_section_error_count += 4  # Count as 4 frequency related errors
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'logic_check_failed',
                        'message': f"无法对信道类型 '{user_channel_type}' 执行频率逻辑检查。请选择 'uu' 或 'aa'。"
                    })
                    frequencies_parsed = False  # Prevent subsequent frequency logic checks that rely on type

                if frequencies_parsed:
                    # Range checks
                    if not (downlink_min <= user_downlink_start <= downlink_max):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 2,
                            'col_header': report_headers[1],
                            'user_value': f"{user_downlink_start}",
                            'answer_value': f"{user_channel_type} 模式下，下行起始频率应在 {downlink_min}-{downlink_max} 范围内",
                            'message': f"{user_channel_type} 模式下，下行起始频率应在 {downlink_min:.2f}-{downlink_max:.2f} 范围内"
                        })
                    if not (downlink_min <= user_downlink_end <= downlink_max):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 3,
                            'col_header': report_headers[2],
                            'user_value': f"{user_downlink_end}",
                            'answer_value': f"{user_channel_type} 模式下，下行终止频率应在 {downlink_min}-{downlink_max} 范围内",
                            'message': f"{user_channel_type} 模式下，下行终止频率应在 {downlink_min:.2f}-{downlink_max:.2f} 范围内"
                        })

                    if not (uplink_min <= user_uplink_start <= uplink_max):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 4,
                            'col_header': report_headers[3],
                            'user_value': f"{user_uplink_start}",
                            'answer_value': f"{user_channel_type} 模式下，上行起始频率应在 {uplink_min}-{uplink_max} 范围内",
                            'message': f"{user_channel_type} 模式下，上行起始频率应在 {uplink_min:.2f}-{uplink_max:.2f} 范围内"
                        })
                    if not (uplink_min <= user_uplink_end <= uplink_max):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 5,
                            'col_header': report_headers[4],
                            'user_value': f"{user_uplink_end}",
                            'answer_value': f"{user_channel_type} 模式下，上行终止频率应在 {uplink_min}-{uplink_max} 范围内",
                            'message': f"{user_channel_type} 模式下，上行终止频率应在 {uplink_min:.2f}-{uplink_max:.2f} 范围内"
                        })

                    # Offset checks
                    if not (abs(user_uplink_start - (user_downlink_start + offset)) < tolerance):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'logic_check_failed', 'row': 1, 'col': 4,
                            'col_header': report_headers[3],
                            'user_value': f"{user_uplink_start}",
                            'answer_value': f"{user_channel_type} 模式下应为 下行起始频率+{offset:.2f}",
                            'message': f"上行起始频率({user_uplink_start})与下行起始频率({user_downlink_start})不满足 {user_channel_type} 模式下 {offset:.2f}MHz 的偏移关系。"
                        })
                    if not (abs(user_uplink_end - (user_downlink_end + offset)) < tolerance):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'logic_check_failed', 'row': 1, 'col': 5,
                            'col_header': report_headers[4],
                            'user_value': f"{user_uplink_end}",
                            'answer_value': f"{user_channel_type} 模式下应为 下行终止频率+{offset:.2f}",
                            'message': f"上行终止频率({user_uplink_end})与下行终止频率({user_downlink_end})不满足 {user_channel_type} 模式下 {offset:.2f}MHz 的偏移关系。"
                        })

                    # Specific rule: uplink end should not be greater than downlink start
                    freq_rel_err_count, freq_rel_detailed_errors = _check_uplink_downlink_frequency_rule(
                        friendly_title, 1,
                        user_downlink_start, user_uplink_end,
                        report_headers[1], report_headers[4]
                    )
                    current_section_error_count += freq_rel_err_count
                    current_section_detailed_errors.extend(freq_rel_detailed_errors)

        elif config["check_type"] == _CHECK_TYPE_CHANNEL_SUITE_LOGIC:
            user_channel_suite_df = _df_to_lol(input_values[config["params"][0]])
            user_channel_segment_df = _df_to_lol(input_values[config["params"][1]])
            report_headers = config["report_headers"]
            expected_rows = 2 # TDM和ALOHA两行数据
            expected_cols = 5 # 名称, 速率, 带宽, 上行中心频点, 下行中心频点
            tolerance = 1e-6

            # 新的索引常量
            TDM_ROW_IDX = 0
            ALOHA_ROW_IDX = 1
            RATE_COL_IDX = 1
            BANDWIDTH_COL_IDX = 2
            UPLINK_CENTER_FREQ_COL_IDX = 3
            DOWNLINK_CENTER_FREQ_COL_IDX = 4

            if not isinstance(user_channel_suite_df, list) or len(user_channel_suite_df) != expected_rows or \
                    not all(isinstance(row, list) and len(row) == expected_cols for row in user_channel_suite_df):
                section_format_error = True
                # If format is wrong, count 8 errors for all cells that would otherwise be checked.
                current_section_error_count += 8
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': f"信道套参数表格格式错误或行/列数不匹配。应为 {expected_rows} 行 {expected_cols} 列。"
                })

            if not section_format_error:
                segment_downlink_start_freq = None
                segment_uplink_start_freq = None
                segment_frequencies_valid = True

                # 尝试从信道段参数获取频率数据
                if not isinstance(user_channel_segment_df, list) or len(user_channel_segment_df) < 1 or \
                        not isinstance(user_channel_segment_df[0], list) or len(user_channel_segment_df[0]) < 4:
                    segment_frequencies_valid = False
                    current_section_error_count += 4 # 4个频点检查无法进行
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'logic_check_failed',
                        'message': "无法获取信道段参数中的频率数据，请检查信道段参数表格格式及内容是否完整。"
                    })
                else:
                    try:
                        # Indexing based on _CHANNEL_SEGMENT_HEADERS: ["卫星名称", "下行起始频率（khz）", "下行终止频率（khz）", "上行起始频率（khz）", "上行终止频率（khz）"]
                        segment_downlink_start_freq = float(str(user_channel_segment_df[0][1]).strip())
                        segment_uplink_start_freq = float(str(user_channel_segment_df[0][3]).strip())
                    except (ValueError, TypeError):
                        segment_frequencies_valid = False
                        current_section_error_count += 4 # 4个频点检查无法进行
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'data_type_error',
                            'message': "信道段参数中的频率值应为数字，无法进行信道套参数的频点逻辑校验。"
                        })

                expected_rate = 9.6
                expected_bandwidth = 100

                # --- TDM 行 (索引 TDM_ROW_IDX) ---
                # TDM 速率检查
                user_rate_tdm_val = str(user_channel_suite_df[TDM_ROW_IDX][RATE_COL_IDX]).strip()
                try:
                    if abs(float(user_rate_tdm_val) - expected_rate) > tolerance:
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'dataframe_cell',
                            'row': TDM_ROW_IDX + 1, 'col': RATE_COL_IDX + 1,
                            'col_header': report_headers[RATE_COL_IDX],
                            'user_value': user_rate_tdm_val,
                            'answer_value': str(expected_rate),
                            'message': f"TDM速率应为 {expected_rate}"
                        })
                except (ValueError, TypeError):
                    current_section_error_count += 1
                    current_section_detailed_errors.append({
                        'section_title': friendly_title, 'type': 'data_type_error',
                        'row': TDM_ROW_IDX + 1, 'col': RATE_COL_IDX + 1,
                        'col_header': report_headers[RATE_COL_IDX],
                        'message': f"TDM速率 '{user_rate_tdm_val}' 应为数字。"
                    })

                # TDM 带宽检查
                user_bandwidth_tdm_val = str(user_channel_suite_df[TDM_ROW_IDX][BANDWIDTH_COL_IDX]).strip()
                try:
                    if abs(float(user_bandwidth_tdm_val) - expected_bandwidth) > tolerance:
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'dataframe_cell',
                            'row': TDM_ROW_IDX + 1, 'col': BANDWIDTH_COL_IDX + 1,
                            'col_header': report_headers[BANDWIDTH_COL_IDX],
                            'user_value': user_bandwidth_tdm_val,
                            'answer_value': str(expected_bandwidth),
                            'message': f"TDM带宽应为 {expected_bandwidth}"
                        })
                except (ValueError, TypeError):
                    current_section_error_count += 1
                    current_section_detailed_errors.append({
                        'section_title': friendly_title, 'type': 'data_type_error',
                        'row': TDM_ROW_IDX + 1, 'col': BANDWIDTH_COL_IDX + 1,
                        'col_header': report_headers[BANDWIDTH_COL_IDX],
                        'message': f"TDM带宽 '{user_bandwidth_tdm_val}' 应为数字。"
                    })

                if segment_frequencies_valid:
                    # TDM 上行中心频点检查
                    expected_tdm_uplink_center_freq = segment_uplink_start_freq + 50
                    user_tdm_uplink_center_freq_val = str(user_channel_suite_df[TDM_ROW_IDX][UPLINK_CENTER_FREQ_COL_IDX]).strip()
                    try:
                        if abs(float(user_tdm_uplink_center_freq_val) - expected_tdm_uplink_center_freq) > tolerance:
                            current_section_error_count += 1
                            current_section_detailed_errors.append({
                                'section_title': friendly_title,
                                'type': 'dataframe_cell',
                                'row': TDM_ROW_IDX + 1, 'col': UPLINK_CENTER_FREQ_COL_IDX + 1,
                                'col_header': report_headers[UPLINK_CENTER_FREQ_COL_IDX],
                                'user_value': user_tdm_uplink_center_freq_val,
                                'answer_value': f"{expected_tdm_uplink_center_freq:.2f}",
                                'message': f"TDM上行中心频点应为 信道段上行起始频率({segment_uplink_start_freq:.2f}) + 50 = {expected_tdm_uplink_center_freq:.2f}"
                            })
                    except (ValueError, TypeError):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'data_type_error',
                            'row': TDM_ROW_IDX + 1, 'col': UPLINK_CENTER_FREQ_COL_IDX + 1,
                            'col_header': report_headers[UPLINK_CENTER_FREQ_COL_IDX],
                            'message': f"TDM上行中心频点 '{user_tdm_uplink_center_freq_val}' 应为数字。"
                        })

                    # TDM 下行中心频点检查 (新增规则：基于下行起始频率+50)
                    expected_tdm_downlink_center_freq = segment_downlink_start_freq + 50
                    user_tdm_downlink_center_freq_val = str(user_channel_suite_df[TDM_ROW_IDX][DOWNLINK_CENTER_FREQ_COL_IDX]).strip()
                    try:
                        if abs(float(user_tdm_downlink_center_freq_val) - expected_tdm_downlink_center_freq) > tolerance:
                            current_section_error_count += 1
                            current_section_detailed_errors.append({
                                'section_title': friendly_title,
                                'type': 'dataframe_cell',
                                'row': TDM_ROW_IDX + 1, 'col': DOWNLINK_CENTER_FREQ_COL_IDX + 1,
                                'col_header': report_headers[DOWNLINK_CENTER_FREQ_COL_IDX],
                                'user_value': user_tdm_downlink_center_freq_val,
                                'answer_value': f"{expected_tdm_downlink_center_freq:.2f}",
                                'message': f"TDM下行中心频点应为 信道段下行起始频率({segment_downlink_start_freq:.2f}) + 50 = {expected_tdm_downlink_center_freq:.2f}"
                            })
                    except (ValueError, TypeError):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'data_type_error',
                            'row': TDM_ROW_IDX + 1, 'col': DOWNLINK_CENTER_FREQ_COL_IDX + 1,
                            'col_header': report_headers[DOWNLINK_CENTER_FREQ_COL_IDX],
                            'message': f"TDM下行中心频点 '{user_tdm_downlink_center_freq_val}' 应为数字。"
                        })
                else:
                    current_section_error_count += 2 # For the 2 TDM center freqs that couldn't be checked
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'logic_check_failed',
                        'message': "因信道段频率数据缺失或格式错误，无法校验TDM中心频点。请先修正信道段参数。"
                    })


                # --- ALOHA 行 (索引 ALOHA_ROW_IDX) ---
                # ALOHA 速率检查
                user_rate_aloha_val = str(user_channel_suite_df[ALOHA_ROW_IDX][RATE_COL_IDX]).strip()
                try:
                    if abs(float(user_rate_aloha_val) - expected_rate) > tolerance:
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'dataframe_cell',
                            'row': ALOHA_ROW_IDX + 1, 'col': RATE_COL_IDX + 1,
                            'col_header': report_headers[RATE_COL_IDX],
                            'user_value': user_rate_aloha_val,
                            'answer_value': str(expected_rate),
                            'message': f"ALOHA速率应为 {expected_rate}"
                        })
                except (ValueError, TypeError):
                    current_section_error_count += 1
                    current_section_detailed_errors.append({
                        'section_title': friendly_title, 'type': 'data_type_error',
                        'row': ALOHA_ROW_IDX + 1, 'col': RATE_COL_IDX + 1,
                        'col_header': report_headers[RATE_COL_IDX],
                        'message': f"ALOHA速率 '{user_rate_aloha_val}' 应为数字。"
                    })

                # ALOHA 带宽检查
                user_bandwidth_aloha_val = str(user_channel_suite_df[ALOHA_ROW_IDX][BANDWIDTH_COL_IDX]).strip()
                try:
                    if abs(float(user_bandwidth_aloha_val) - expected_bandwidth) > tolerance:
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'dataframe_cell',
                            'row': ALOHA_ROW_IDX + 1, 'col': BANDWIDTH_COL_IDX + 1,
                            'col_header': report_headers[BANDWIDTH_COL_IDX],
                            'user_value': user_bandwidth_aloha_val,
                            'answer_value': str(expected_bandwidth),
                            'message': f"ALOHA带宽应为 {expected_bandwidth}"
                        })
                except (ValueError, TypeError):
                    current_section_error_count += 1
                    current_section_detailed_errors.append({
                        'section_title': friendly_title, 'type': 'data_type_error',
                        'row': ALOHA_ROW_IDX + 1, 'col': BANDWIDTH_COL_IDX + 1,
                        'col_header': report_headers[BANDWIDTH_COL_IDX],
                        'message': f"ALOHA带宽 '{user_bandwidth_aloha_val}' 应为数字。"
                    })

                if segment_frequencies_valid:
                    # ALOHA 上行中心频点检查 (新增规则：基于上行起始频率+150)
                    expected_aloha_uplink_center_freq = segment_uplink_start_freq + 150
                    user_aloha_uplink_center_freq_val = str(user_channel_suite_df[ALOHA_ROW_IDX][UPLINK_CENTER_FREQ_COL_IDX]).strip()
                    try:
                        if abs(float(user_aloha_uplink_center_freq_val) - expected_aloha_uplink_center_freq) > tolerance:
                            current_section_error_count += 1
                            current_section_detailed_errors.append({
                                'section_title': friendly_title,
                                'type': 'dataframe_cell',
                                'row': ALOHA_ROW_IDX + 1, 'col': UPLINK_CENTER_FREQ_COL_IDX + 1,
                                'col_header': report_headers[UPLINK_CENTER_FREQ_COL_IDX],
                                'user_value': user_aloha_uplink_center_freq_val,
                                'answer_value': f"{expected_aloha_uplink_center_freq:.2f}",
                                'message': f"ALOHA上行中心频点应为 信道段上行起始频率({segment_uplink_start_freq:.2f}) + 150 = {expected_aloha_uplink_center_freq:.2f}"
                            })
                    except (ValueError, TypeError):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'data_type_error',
                            'row': ALOHA_ROW_IDX + 1, 'col': UPLINK_CENTER_FREQ_COL_IDX + 1,
                            'col_header': report_headers[UPLINK_CENTER_FREQ_COL_IDX],
                            'message': f"ALOHA上行中心频点 '{user_aloha_uplink_center_freq_val}' 应为数字。"
                        })

                    # ALOHA 下行中心频点检查
                    expected_aloha_downlink_center_freq = segment_downlink_start_freq + 150
                    user_aloha_downlink_center_freq_val = str(user_channel_suite_df[ALOHA_ROW_IDX][DOWNLINK_CENTER_FREQ_COL_IDX]).strip()
                    try:
                        if abs(float(user_aloha_downlink_center_freq_val) - expected_aloha_downlink_center_freq) > tolerance:
                            current_section_error_count += 1
                            current_section_detailed_errors.append({
                                'section_title': friendly_title,
                                'type': 'dataframe_cell',
                                'row': ALOHA_ROW_IDX + 1, 'col': DOWNLINK_CENTER_FREQ_COL_IDX + 1,
                                'col_header': report_headers[DOWNLINK_CENTER_FREQ_COL_IDX],
                                'user_value': user_aloha_downlink_center_freq_val,
                                'answer_value': f"{expected_aloha_downlink_center_freq:.2f}",
                                'message': f"ALOHA下行中心频点应为 信道段下行起始频率({segment_downlink_start_freq:.2f}) + 150 = {expected_aloha_downlink_center_freq:.2f}"
                            })
                    except (ValueError, TypeError):
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'data_type_error',
                            'row': ALOHA_ROW_IDX + 1, 'col': DOWNLINK_CENTER_FREQ_COL_IDX + 1,
                            'col_header': report_headers[DOWNLINK_CENTER_FREQ_COL_IDX],
                            'message': f"ALOHA下行中心频点 '{user_aloha_downlink_center_freq_val}' 应为数字。"
                        })
                else:
                    current_section_error_count += 2 # For the 2 ALOHA center freqs that couldn't be checked
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'logic_check_failed',
                        'message': "因信道段频率数据缺失或格式错误，无法校验ALOHA中心频点。请先修正信道段参数。"
                    })

        elif config["check_type"] == _CHECK_TYPE_VIRTUAL_SUBNET_LOGIC:
            user_df_value = _df_to_lol(input_values[config["params"][0]])
            user_selected_rate = input_values[config["params"][1]]
            report_headers = config["report_headers"]

            expected_rows = 1
            expected_cols = 6

            if not isinstance(user_df_value, list) or len(user_df_value) != expected_rows or \
                    not all(isinstance(row, list) and len(row) == expected_cols for row in user_df_value):
                section_format_error = True
                current_section_error_count += 2 # Count for the 2 main logic checks (bandwidth/frequency overlap)
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': f"虚拟子网参数表格格式错误或行/列数不匹配。应为 {expected_rows} 行 {expected_cols} 列。"
                })

            if not section_format_error:
                user_row = user_df_value[0]

                BW_COL_IDX = 1
                DL_START_FREQ_COL_IDX = 2
                DL_END_FREQ_COL_IDX = 3
                UL_START_FREQ_COL_IDX = 4
                UL_END_FREQ_COL_IDX = 5

                user_bandwidth_val = user_row[BW_COL_IDX]
                user_dl_start = user_row[DL_START_FREQ_COL_IDX]
                user_dl_end = user_row[DL_END_FREQ_COL_IDX]
                user_ul_start = user_row[UL_START_FREQ_COL_IDX]
                user_ul_end = user_row[UL_END_FREQ_COL_IDX]

                if user_selected_rate is None:
                    current_section_error_count += 1
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'logic_check_failed',
                        'message': "请选择一个虚拟子网速率，以便校验带宽。"
                    })
                else:
                    bw_rate_err_count, bw_rate_detailed_errors = _check_bandwidth_vs_rate_rule(
                        friendly_title, 1,
                        user_selected_rate, user_bandwidth_val,
                        "选择速率", report_headers[BW_COL_IDX], _KBP_MAPPING
                    )
                    current_section_error_count += bw_rate_err_count
                    current_section_detailed_errors.extend(bw_rate_detailed_errors)

                freq_overlap_err_count, freq_overlap_detailed_errors = _check_frequency_overlap_rule(
                    friendly_title, 1,
                    user_dl_start, user_dl_end, user_ul_start, user_ul_end,
                    report_headers[DL_START_FREQ_COL_IDX], report_headers[DL_END_FREQ_COL_IDX],
                    report_headers[UL_START_FREQ_COL_IDX], report_headers[UL_END_FREQ_COL_IDX]
                )
                current_section_error_count += freq_overlap_err_count
                current_section_detailed_errors.extend(freq_overlap_detailed_errors)


        elif config["check_type"] == _CHECK_TYPE_TEXTBOX_AND_DATAFRAME:
            user_df_value = _df_to_lol(input_values[config["params"][-1]])
            report_headers = config["report_headers"]
            # NOTE: The textbox values (local_cc_address_value, remote_xx_address_value) are captured but not
            # explicitly checked for correctness here against 'correct_textbox_answers' as per the design evolution.
            # Only the dataframe content and its logic are currently being graded in this block.

            if not isinstance(user_df_value, list) or not all(isinstance(row, list) for row in user_df_value):
                section_format_error = True
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': "点对点通信参数表格格式错误或无法解析。请确保输入为有效数据。"
                })

            if not section_format_error:
                user_rows = len(user_df_value)
                expected_rows = 2
                if user_rows != expected_rows:
                    # Each row is expected to have two main checks (frequency rule and bandwidth rule)
                    # So, if a row is missing, consider it 2 errors for that row.
                    current_section_error_count += abs(user_rows - expected_rows) * 2
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'row_count_mismatch',
                        'message': f"表格行数不匹配: 您的表格有 {user_rows} 行，应有 {expected_rows} 行。",
                        'user_value': str(user_rows),
                        'answer_value': str(expected_rows)
                    })
                rows_to_compare = min(user_rows, expected_rows)

                p2p_rate_idx = _P2P_RATE_COL_INDEX
                p2p_bandwidth_idx = _P2P_BANDWIDTH_COL_INDEX
                p2p_downlink_start_idx = _P2P_DOWNLINK_START_COL_INDEX
                p2p_uplink_end_idx = _P2P_UPLINK_END_COL_INDEX

                for r in range(rows_to_compare):
                    user_row = user_df_value[r]
                    min_cols_needed = max(p2p_rate_idx, p2p_bandwidth_idx, p2p_downlink_start_idx,
                                          p2p_uplink_end_idx) + 1
                    if len(user_row) < min_cols_needed:
                        current_section_error_count += 2 # Count 2 errors for missing critical columns
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'column_count_mismatch',
                            'row': r + 1,
                            'message': f"第 {r + 1} 行列数不足，缺少必要的频率或带宽/速率列，无法进行校验。"
                        })
                        continue

                    # Check uplink/downlink frequency rule (UL_End > DL_Start)
                    if p2p_downlink_start_idx < len(user_row) and p2p_uplink_end_idx < len(user_row):
                        dl_start_val = user_row[p2p_downlink_start_idx]
                        ul_end_val = user_row[p2p_uplink_end_idx]

                        freq_rel_err_count, freq_rel_detailed_errors = _check_uplink_downlink_frequency_rule(
                            friendly_title, r + 1,
                            dl_start_val, ul_end_val,
                            report_headers[p2p_downlink_start_idx], report_headers[p2p_uplink_end_idx]
                        )
                        current_section_error_count += freq_rel_err_count
                        current_section_detailed_errors.extend(freq_rel_detailed_errors)
                    else:
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'column_count_mismatch',
                            'row': r + 1,
                            'message': f"第 {r + 1} 行频率列缺失，无法进行上行/下行频点逻辑校验。"
                        })

                    # Check bandwidth vs rate rule
                    if p2p_rate_idx < len(user_row) and p2p_bandwidth_idx < len(user_row):
                        user_rate_val = user_row[p2p_rate_idx]
                        user_bandwidth_val = user_row[p2p_bandwidth_idx]

                        bw_rate_err_count, bw_rate_detailed_errors = _check_bandwidth_vs_rate_rule(
                            friendly_title, r + 1,
                            user_rate_val, user_bandwidth_val,
                            report_headers[p2p_rate_idx], report_headers[p2p_bandwidth_idx], _KBP_MAPPING
                        )
                        current_section_error_count += bw_rate_err_count
                        current_section_detailed_errors.extend(bw_rate_detailed_errors)
                    else:
                        current_section_error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'column_count_mismatch',
                            'row': r + 1,
                            'message': f"第 {r + 1} 行速率或带宽列缺失，无法进行带宽速率校验。"
                        })

        else:
            print(
                f"Warning: Unsupported check type '{config['check_type']}' for section '{friendly_title}'. Cannot count errors.")
            current_section_detailed_errors.append({
                'section_title': friendly_title,
                'type': 'unsupported_check_type',
                'message': f"此部分使用了不支持的检查类型 '{config['check_type']}'。"
            })

        if current_section_detailed_errors:
            error_sections_with_counts.append((friendly_title, len(current_section_detailed_errors)))

            if friendly_title not in error_titles_only:
                error_titles_only.append(friendly_title)

            detailed_errors.extend(current_section_detailed_errors)

    if not error_sections_with_counts:
        error_message_string = "恭喜，答卷全部正确！"
    else:
        error_message_string = "以下部分填写有误：\n\n"
        for title, count in error_sections_with_counts:
            error_message_string += f"- **{title}**：错误个数：{count}\n"

        if detailed_errors:
            error_message_string += "\n请参考下面的**详细错误列表**查看具体差异。"

    return (error_message_string, error_sections_with_counts, error_titles_only, detailed_errors)