# checker.py

import io
import sys
import os
import pandas as pd
from collections import defaultdict  # Import defaultdict for duplicate checking

# --- 静态标签定义 (用于生成输出字符串，确保与主文件界面上的标签一致) ---
_SUBNET_ID_LABEL = "子网编号："
_NETWORK_NAME_LABEL = "网络名称："
_LOCAL_CC_ADDRESS_LABEL = "本端CC地址:"
_REMOTE_XX_ADDRESS_LABEL = "对端XX地址："
_CHANNEL_TYPE_LABEL = "信道类型选择："  # 新增标签

# --- 静态的正确答案定义 ---
# 移除了 (1) xx参数 和 (2) Xxx站配置参数 的正确答案定义，因为它们不再计入成绩。

# (3) 信道段参数 (NOTE: Specific values are now logic-dependent, not fixed here)
_CHANNEL_SEGMENT_HEADERS = ["卫星名称", "下行起始频率（khz）", "下行终止频率（khz）", "上行起始频率（khz）",
                            "上行终止频率（khz）"]
_CHANNEL_SEGMENT_FILLABLE_COLS_INDICES = [1, 2, 3, 4]  # Assuming 卫星名称是预填的，用户填写频率
_CORRECT_CHANNEL_TYPE = "uu"  # 假设正确的信道类型是 "uu"

# (4) 信道套参数
_CORRECT_CHANNEL_SUITE_VALUES = [
    ["信道段", "10", "20"],  # TDM, ALOHA
    ["速率", "100", "200"],
    ["中心频点", "1500", "3500"],
    ["带宽", "50", "100"],
]
_CHANNEL_SUITE_HEADERS = ["名称", "TDM", "ALOHA"]
_CHANNEL_SUITE_FILLABLE_COLS_INDICES = [1, 2]  # Assuming "名称" 是预填的

# 1.组网参数分析 - 正确答案定义已不再用于此部分，因为检查逻辑改变为检查重复
# 保留 headers 以便报告使用
_NETWORK_ANALYSIS_HEADERS = ["用户单位", "站型", "站地址", "CC地址", "电话号码", "设备序列号"]
# _NETWORK_ANALYSIS_FILLABLE_COLS_INDICES = [1, 2, 3, 4] # 不再需要这个用于计分

# 2.点对点通信参数
# IMPORTANT: Correct answers for specific values are NOT defined here, as they are no longer checked for exact match.
# Only KBP and frequency relationship rules apply.
# _CORRECT_LOCAL_CC_ADDRESS and _CORRECT_REMOTE_XX_ADDRESS are KEPT as placeholders,
# but their comparison logic is removed in check_paper for this section.
_CORRECT_LOCAL_CC_ADDRESS = "192.168.1.100"  # Placeholder, no longer checked for exact match
_CORRECT_REMOTE_XX_ADDRESS = "10.0.0.1"  # Placeholder, no longer checked for exact match

_P2P_HEADERS = ["名称", "速率kbps", "带宽（khz）", "下行起始频点（khz）", "下行终止频点（khz）", "上行起始频点（khz）",
                "上行终止频点（khz）"]
# Column indices for P2P table values that are relevant for new logic checks
_P2P_RATE_COL_INDEX = 1
_P2P_BANDWIDTH_COL_INDEX = 2
_P2P_DOWNLINK_START_COL_INDEX = 3
_P2P_UPLINK_END_COL_INDEX = 6

# 3.虚拟子网参数
_CORRECT_VIRTUAL_SUBNET_VALUES = [
    ["虚拟子网信道段", "1000", "10000", "11000", "12000", "13000"],  # Bandwidth, Frequencies
]
_VIRTUAL_SUBNET_HEADERS = ["名称", "带宽（khz）", "下行起始频率（khz）", "下行终止频率（khz）", "上行起始频率（khz）",
                           "上行终止频率（khz）"]
_VIRTUAL_SUBNET_FILLABLE_COLS_INDICES = [1, 2, 3, 4, 5]  # Excluding "名称" column

# --- Check Type Constants ---
_CHECK_TYPE_TEXTBOX_GROUP = "textbox_group"
_CHECK_TYPE_DATAFRAME = "dataframe"
_CHECK_TYPE_CHANNEL_FREQUENCY_LOGIC = "channel_frequency_logic"
_CHECK_TYPE_TEXTBOX_AND_DATAFRAME = "textbox_and_dataframe"  # This type is reused for P2P but with modified logic
_CHECK_TYPE_DATAFRAME_COLUMN_DUPLICATE = "dataframe_column_duplicate_check"  # 新增的检查类型

# --- 用于比较的逻辑段落配置 (移除了 (1) 和 (2) 部分) ---
_COMPARISON_CONFIG = {
    # 移除了 "(1) xx参数"
    # 移除了 "(2) Xxx站配置参数"
    "（3）信道段参数": {
        "check_type": _CHECK_TYPE_CHANNEL_FREQUENCY_LOGIC,  # New custom check type
        "report_headers": _CHANNEL_SEGMENT_HEADERS,
        "dropdown_label": _CHANNEL_TYPE_LABEL,
        "correct_dropdown_value": _CORRECT_CHANNEL_TYPE,  # Still useful for base check
        "params": ["channel_segment_value", "channel_type_value"]  # dataframe first, then dropdown
    },
    "（4）信道套参数": {
        "check_type": _CHECK_TYPE_DATAFRAME,
        "report_headers": _CHANNEL_SUITE_HEADERS,
        "correct_values": _CORRECT_CHANNEL_SUITE_VALUES,
        "fillable_cols_indices": _CHANNEL_SUITE_FILLABLE_COLS_INDICES,
        "param": "channel_suite_value"
    },
    "1.组网参数分析": {
        "check_type": _CHECK_TYPE_DATAFRAME_COLUMN_DUPLICATE,  # 使用新的检查类型
        "report_headers": _NETWORK_ANALYSIS_HEADERS,  # 仍然需要 headers 用于报告
        "param": "network_analysis_value",
        "column_to_check_index": 3,  # "CC地址" 列的索引 (0-based)
        "column_to_check_name": "CC地址"  # 方便在详细错误中显示列名
        # 不再需要 correct_values 和 fillable_cols_indices
    },
    "2.点对点通信参数": {
        "check_type": _CHECK_TYPE_TEXTBOX_AND_DATAFRAME,  # Revert to this type, but modify its logic
        "fields": [_LOCAL_CC_ADDRESS_LABEL, _REMOTE_XX_ADDRESS_LABEL],  # Keep for parsing, but not for exact check
        "correct_textbox_answers": [_CORRECT_LOCAL_CC_ADDRESS, _CORRECT_REMOTE_XX_ADDRESS],
        # Keep as placeholders, not for exact check
        "report_headers": _P2P_HEADERS,
        # No correct_dataframe_values needed for exact match
        "fillable_cols_indices": _P2P_FILLABLE_COLS_INDICES,
        # Keep for consistency in structure checks if needed, but not for exact cell matching
        "params": ["local_cc_address_value", "remote_xx_address_value", "p2p_value"]
    },
    "3.虚拟子网参数": {
        "check_type": _CHECK_TYPE_DATAFRAME,
        "report_headers": _VIRTUAL_SUBNET_HEADERS,
        "correct_values": _CORRECT_VIRTUAL_SUBNET_VALUES,
        "fillable_cols_indices": _VIRTUAL_SUBNET_FILLABLE_COLS_INDICES,
        "param": "virtual_subnet_value"
    }
}

# --- KBP映射全局变量 ---
_KBP_MAPPING = {}
_KBP_FILE_LOADED = False
_KBP_LOAD_ERROR = None  # This will store the error message if loading fails


def _load_kbp_mapping():
    """
    从kbp.txt文件加载速率与带宽的对应关系。
    格式: 速率:带宽 (例如: 32:42)
    """
    global _KBP_MAPPING, _KBP_FILE_LOADED, _KBP_LOAD_ERROR
    # Reset states for a fresh load attempt
    _KBP_MAPPING = {}
    _KBP_FILE_LOADED = False
    _KBP_LOAD_ERROR = None

    kbp_file_path = 'kbp.txt'  # Assuming kbp.txt is in the root directory
    if not os.path.exists(kbp_file_path):
        _KBP_LOAD_ERROR = f"错误: 缺少kbp.txt文件。请确保文件存在于 {os.getcwd()}。"
        print(_KBP_LOAD_ERROR)
        return

    try:
        temp_mapping = {}
        with open(kbp_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                try:
                    rate_str, bandwidth_str = line.split(':')
                    rate = int(rate_str.strip())
                    bandwidth = int(bandwidth_str.strip())
                    temp_mapping[rate] = bandwidth
                except ValueError:
                    if _KBP_LOAD_ERROR is None:  # Initialize error string if it's the first error
                        _KBP_LOAD_ERROR = ""
                    _KBP_LOAD_ERROR += f"警告: kbp.txt中存在格式错误的行: '{line}'，已跳过。正确格式应为 '速率:带宽' (例如: 32:42)。\n"
                    print(f"警告: kbp.txt中存在格式错误的行: '{line}'，已跳过。")
                except Exception as e:
                    if _KBP_LOAD_ERROR is None:  # Initialize error string if it's the first error
                        _KBP_LOAD_ERROR = ""
                    _KBP_LOAD_ERROR += f"警告: 读取kbp.txt时发生未知错误: {e} 在行 '{line}'。\n"
                    print(f"读取kbp.txt时发生未知错误: {e} 在行 '{line}'。")

        _KBP_MAPPING = temp_mapping
        _KBP_FILE_LOADED = True
        if not _KBP_MAPPING and _KBP_LOAD_ERROR is None:  # If file was empty but no parsing errors
            _KBP_LOAD_ERROR = "警告: kbp.txt文件为空或未包含有效数据。"
            print(_KBP_LOAD_ERROR)

    except Exception as e:  # Catch file opening errors etc.
        _KBP_LOAD_ERROR = f"无法读取kbp.txt文件: {e}"
        _KBP_FILE_LOADED = False  # Indicate that file could not be fully loaded/parsed
        print(_KBP_LOAD_ERROR)


# --- 函数 1: 捕获用户输入并格式化为字符串 (用于下载，功能不变) ---
def capture_paper_data_string(
        subnet_id_value, network_name_value,
        station_config_headers, station_config_value,  # station_config_value 是 DataFrame
        channel_segment_headers, channel_segment_value,  # channel_segment_value 是 DataFrame
        channel_suite_headers, channel_suite_value,  # channel_suite_value 是 DataFrame
        network_analysis_headers, network_analysis_value,  # network_analysis_value 是 DataFrame
        local_cc_address_value, remote_xx_address_value,
        p2p_headers, p2p_value,  # p2p_value 是 DataFrame
        virtual_subnet_headers, virtual_subnet_value,  # virtual_subnet_value 是 DataFrame
        channel_type_value  # 新增参数
):
    """
    捕获所有用户输入数据，并将其格式化为可读的字符串，用于下载保存。

    Args:
        各项直接从 Gradio 界面接收的用户输入值。

    Returns:
        str: 格式化后的用户输入数据字符串。
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
        # 转换 DataFrame 为 list of lists
        station_config_list = station_config_value.values.tolist() if isinstance(station_config_value,
                                                                                 pd.DataFrame) else station_config_value
        print("Data:", station_config_list)

        print(f"\n(3) 信道段参数:")
        print("Headers:", channel_segment_headers)
        channel_segment_list = channel_segment_value.values.tolist() if isinstance(channel_segment_value,
                                                                                   pd.DataFrame) else channel_segment_value
        print("Data:", channel_segment_list)
        print(f"{_CHANNEL_TYPE_LABEL} {channel_type_value}")  # 在此处打印新增的信道类型值

        print(f"\n(4) 信道套参数:")
        print("Headers:", channel_suite_headers)
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
        print("Headers:", p2p_headers)
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
    """
    检查上行终止频率是否大于下行起始频率。
    如果发现错误，返回错误个数和详细错误列表。
    Args:
        section_title (str): 错误所属的友好标题。
        user_row_index (int): 1-based 行索引。
        downlink_start_freq_val (str/float): 用户填写的下行起始频率值。
        uplink_end_freq_val (str/float): 用户填写的上行终止频率值。
        downlink_start_col_header (str): 下行起始频率的列头。
        uplink_end_col_header (str): 上行终止频率的列头。
    Returns:
        tuple: (error_count, detailed_error_list)
    """
    errors = []
    error_count = 0
    try:
        # 尝试将频率值转换为浮点数进行比较
        dl_start = float(str(downlink_start_freq_val).strip())
        ul_end = float(str(uplink_end_freq_val).strip())

        if ul_end > dl_start:
            error_count += 1
            errors.append({
                'section_title': section_title,
                'type': 'frequency_logic_error',
                'row': user_row_index,
                'col_header_ul_end': uplink_end_col_header,  # For display in markdown
                'col_header_dl_start': downlink_start_col_header,  # For display in markdown
                'user_value_ul_end': f"{ul_end:.2f}",
                'user_value_dl_start': f"{dl_start:.2f}",
                'message': f"上行终止频率 ({ul_end:.2f}khz) 不应大于下行起始频率 ({dl_start:.2f}khz)。"
            })
    except (ValueError, TypeError):
        # 如果频率值不是有效的数字，这个错误应该由其他类型（如 data_type_error）捕获。
        # 此处不重复计数，避免双重惩罚。
        pass
    return error_count, errors


# 新增辅助函数：检查带宽是否大于等于对应速率的带宽
def _check_bandwidth_vs_rate_rule(section_title, user_row_index, user_rate_val, user_bandwidth_val,
                                  rate_col_header, bandwidth_col_header):
    """
    检查带宽是否大于等于kbp.txt中对应速率的带宽值。
    如果发现错误，返回错误个数和详细错误列表。
    Args:
        section_title (str): 错误所属的友好标题。
        user_row_index (int): 1-based 行索引。
        user_rate_val (str/int): 用户填写的速率值。
        user_bandwidth_val (str/int): 用户填写的带宽值。
        rate_col_header (str): 速率列的列头。
        bandwidth_col_header (str): 带宽列的列头。
    Returns:
        tuple: (error_count, detailed_error_list)
    """
    errors = []
    error_count = 0

    # 检查KBP文件加载状态
    if not _KBP_FILE_LOADED:
        error_count += 1
        errors.append({
            'section_title': section_title,
            'type': 'kbp_load_error',
            'message': _KBP_LOAD_ERROR if _KBP_LOAD_ERROR else "KBP映射文件未加载或为空，无法进行带宽速率校验。"
        })
        return error_count, errors

    # 如果文件加载成功但映射为空（例如文件内容只有注释或无效行）
    if not _KBP_MAPPING:
        error_count += 1
        errors.append({
            'section_title': section_title,
            'type': 'kbp_load_error',
            'message': _KBP_LOAD_ERROR if _KBP_LOAD_ERROR else "KBP映射文件为空或未包含有效数据，无法进行带宽速率校验。"
        })
        return error_count, errors

    try:
        user_rate = int(str(user_rate_val).strip())
        user_bandwidth = int(str(user_bandwidth_val).strip())

        if user_rate not in _KBP_MAPPING:
            error_count += 1
            errors.append({
                'section_title': section_title,
                'type': 'bandwidth_rate_mismatch',
                'row': user_row_index,
                'col_header_rate': rate_col_header,
                'col_header_bandwidth': bandwidth_col_header,
                'user_value_rate': f"{user_rate}",
                'user_value_bandwidth': f"{user_bandwidth}",
                'message': f"速率 '{user_rate}' 在KBP映射文件中未找到对应带宽。请核对速率值。"
            })
        else:
            required_bandwidth = _KBP_MAPPING[user_rate]
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
        # 如果速率或带宽值不是有效的数字，这个错误应该由dataframe_cell或data_type_error捕获。
        # 此处专注于逻辑检查，假设输入类型正确。
        pass
    except Exception as e:
        error_count += 1
        errors.append({
            'section_title': section_title,
            'type': 'bandwidth_rate_mismatch',
            'row': user_row_index,
            'message': f"带宽与速率对应关系检查时发生内部错误: {e}"
        })
    return error_count, errors


# --- 函数 2: 对比用户输出与正确答案并计算错误个数及详细错误 ---
def check_paper(
        subnet_id_value, network_name_value,  # 这些参数仍然接收，但不再被用于评分
        station_config_value,  # 这些参数仍然接收，但不再被用于评分
        channel_segment_value, channel_type_value,
        channel_suite_value,
        network_analysis_value,
        local_cc_address_value, remote_xx_address_value, p2p_value,
        virtual_subnet_value
):
    """
    将用户答卷结果直接与内置的正确答案/逻辑进行对比，计算并返回错误个数、错误部分的标题列表，
    以及详细的错误信息列表。

    Args:
        各项直接从 Gradio 界面接收的用户输入值。

    Returns:
        tuple: (error_message_string, list_of_error_titles_with_counts, list_of_error_titles_only, detailed_errors_list)
               error_message_string (str): 包含错误部分标题和个数的格式化字符串，或表示全部正确的字符串。
               list_of_error_titles_with_counts (list[tuple]): 错误部分的友好标题和错误个数的列表 (例如: [("（1）xx参数", 2), ...])。
               list_of_error_titles_only (list[str]): 错误部分的友好标题列表 (用于传递给分析器)。
               detailed_errors_list (list[dict]): 详细的错误信息列表，用于页面显示具体错误。
    """
    error_sections_with_counts = []  # List of (title, count) tuples for summary
    error_titles_only = []  # List of titles only for analyzer
    detailed_errors = []  # Stores detailed error information

    # 在检查前先加载KBP映射，确保只加载一次
    _load_kbp_mapping()

    # Use a dictionary to map param names to actual values passed into this function
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
        "virtual_subnet_value": virtual_subnet_value
    }

    # Helper function to convert dataframe to list of lists for consistent comparison
    def _df_to_lol(df_value):
        """Converts a pandas DataFrame to a list of lists, or returns as-is if not a DataFrame."""
        if isinstance(df_value, pd.DataFrame):
            return df_value.values.tolist()
        return df_value  # Already a list of lists or None

    for friendly_title, config in _COMPARISON_CONFIG.items():
        error_count = 0
        current_section_detailed_errors = []  # Errors specific to this section

        if config["check_type"] == _CHECK_TYPE_TEXTBOX_GROUP:
            # This type is currently not used in _COMPARISON_CONFIG as (1) and (2) are ignored.
            # Keeping the logic for completeness, if it were to be re-introduced.
            user_values = [input_values[param] for param in config["params"]]
            correct_answers = config["correct_answers"]
            fields = config["fields"]

            for i in range(len(correct_answers)):
                user_val = str(user_values[i]).strip()
                correct_val = str(correct_answers[i]).strip()
                if user_val != correct_val:
                    error_count += 1
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'textbox',
                        'field_label': fields[i],
                        'user_value': user_val,
                        'answer_value': correct_val
                    })

        elif config["check_type"] == _CHECK_TYPE_DATAFRAME:
            user_df_value = _df_to_lol(input_values[config["param"]])
            correct_values = config["correct_values"]
            fillable_cols_indices = config["fillable_cols_indices"]
            report_headers = config["report_headers"]

            # Validate user input structure
            if not isinstance(user_df_value, list) or not all(isinstance(row, list) for row in user_df_value):
                # If not a list of lists, treat as major format error.
                # Count all possible fillable cells as errors if structure is completely wrong.
                total_expected_errors = len(correct_values) * len(fillable_cols_indices) if fillable_cols_indices else 0
                error_count += total_expected_errors
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': "表格格式错误或无法解析。请确保输入为有效数据。"
                })
                error_sections_with_counts.append((friendly_title, "格式错误或解析失败"))
                error_titles_only.append(friendly_title)
                continue  # Skip detailed comparison for this section

            user_rows = len(user_df_value)
            correct_rows = len(correct_values)

            # Compare row counts
            if user_rows != correct_rows:
                # Calculate errors for missing/extra rows.
                # Here, we count errors for every 'missing' fillable cell or every 'extra' cell.
                # Simplified: if row counts differ, assume the 'correct' cells are missing/wrong in unmatched rows.
                # Only compare common rows to avoid index errors.
                rows_to_compare = min(user_rows, correct_rows)
                # Count errors for missing rows: for each missing correct row, add errors for all its fillable cells.
                if user_rows < correct_rows:
                    error_count += (correct_rows - user_rows) * len(fillable_cols_indices)

                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'row_count_mismatch',
                    'message': f"行数不匹配: 您的表格有 {user_rows} 行，应有 {correct_rows} 行。",
                    'user_value': str(user_rows),
                    'answer_value': str(correct_rows)
                })
            else:
                rows_to_compare = user_rows

            # Identify frequency columns for Virtual Subnet table (if applicable)
            # This is for "3.虚拟子网参数" specifically
            virtual_subnet_downlink_start_idx = 2
            virtual_subnet_uplink_end_idx = 5

            for r in range(rows_to_compare):
                user_row = user_df_value[r]
                # Determine columns to check in the current row based on user's column count
                max_fillable_col_idx = max(fillable_cols_indices) if fillable_cols_indices else -1

                if len(user_row) <= max_fillable_col_idx:
                    # If user row has too few columns, count errors for missing fillable cells *in this row*
                    missing_cols_in_row = len([idx for idx in fillable_cols_indices if idx >= len(user_row)])
                    error_count += missing_cols_in_row
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'column_count_mismatch',
                        'row': r + 1,
                        'message': f"第 {r + 1} 行列数不足，缺少应填写的列。",
                        'user_value': str(len(user_row)),
                        'answer_value': f"至少需要 {max_fillable_col_idx + 1} 列"
                    })
                    cols_to_check_in_row = [idx for idx in fillable_cols_indices if idx < len(user_row)]
                else:
                    cols_to_check_in_row = fillable_cols_indices

                for c_idx in cols_to_check_in_row:
                    # Find the corresponding index in the correct_values row based on the fillable_cols_indices mapping
                    # This assumes correct_values lists only the *fillable* columns in order
                    correct_val_relative_idx = fillable_cols_indices.index(c_idx)

                    user_val = str(user_row[c_idx]).strip()
                    correct_val = str(correct_values[r][correct_val_relative_idx]).strip()

                    if user_val != correct_val:
                        error_count += 1
                        col_header_display = report_headers[c_idx] if c_idx < len(report_headers) else f"列 {c_idx + 1}"
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'dataframe_cell',
                            'row': r + 1,  # 1-based index
                            'col': c_idx + 1,  # 1-based index
                            'col_header': col_header_display,
                            'user_value': user_val,
                            'answer_value': correct_val
                        })

                # NEW: Check for Uplink_End <= Downlink_Start for "3.虚拟子网参数"
                if friendly_title == "3.虚拟子网参数" and \
                        len(user_row) > max(virtual_subnet_downlink_start_idx, virtual_subnet_uplink_end_idx):
                    dl_start_val = user_row[virtual_subnet_downlink_start_idx]
                    ul_end_val = user_row[virtual_subnet_uplink_end_idx]

                    freq_rel_err_count, freq_rel_detailed_errors = _check_uplink_downlink_frequency_rule(
                        friendly_title, r + 1,
                        dl_start_val, ul_end_val,
                        report_headers[virtual_subnet_downlink_start_idx], report_headers[virtual_subnet_uplink_end_idx]
                    )
                    error_count += freq_rel_err_count
                    current_section_detailed_errors.extend(freq_rel_detailed_errors)

        elif config["check_type"] == _CHECK_TYPE_DATAFRAME_COLUMN_DUPLICATE:
            # Logic for 1.组网参数分析 (CC地址 uniqueness)
            user_df_value = _df_to_lol(input_values[config["param"]])
            col_to_check_idx = config["column_to_check_index"]
            col_to_check_name = config["column_to_check_name"]
            report_headers = config["report_headers"]

            if not isinstance(user_df_value, list) or not all(isinstance(row, list) for row in user_df_value):
                # If malformed, treat all possible cells in that column as errors.
                # Assuming 5 rows for this table based on `network_analysis_data`.
                error_count += 5  # 5 potential CC addresses
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': "组网参数分析表格格式错误或无法解析。请确保输入为有效数据。"
                })
                error_sections_with_counts.append((friendly_title, "格式错误或解析失败"))
                error_titles_only.append(friendly_title)
                continue

            value_first_row_map = {}  # Map value to its first occurring row index (0-based)
            duplicate_rows_map = defaultdict(list)  # Map value to list of subsequent row indices (0-based)

            for r, row in enumerate(user_df_value):
                # Ensure row has enough columns to access the target CC address column
                if col_to_check_idx < len(row):
                    cell_value = str(row[col_to_check_idx]).strip()
                    if cell_value and cell_value != "":  # Only check non-empty values for duplication
                        if cell_value in value_first_row_map:
                            duplicate_rows_map[cell_value].append(r)
                        else:
                            value_first_row_map[cell_value] = r
                else:
                    # If a row is too short to contain the CC address, it's a format error for that cell.
                    # This specific error is handled by `dataframe_cell` type check if it were a normal comparison.
                    # For uniqueness, we just won't consider it for duplication.
                    pass  # Not counting missing CC address as a duplicate error, but it might be caught by other checks later if any.

            # Count errors for each duplicate occurrence (excluding the first instance)
            for value, row_indices in duplicate_rows_map.items():
                error_count += len(row_indices)  # Each entry in row_indices is a duplicate
                col_header_display = report_headers[col_to_check_idx] if col_to_check_idx < len(
                    report_headers) else f"列 {col_to_check_idx + 1}"

                for dup_r in row_indices:
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'dataframe_duplicate',  # New type for duplicate errors
                        'row': dup_r + 1,  # 1-based index
                        'col': col_to_check_idx + 1,  # 1-based index
                        'col_header': col_header_display,
                        'user_value': value,
                        'message': f"值 '{value}' 在此行重复出现。CC地址列不允许重复。"
                    })

        elif config["check_type"] == _CHECK_TYPE_CHANNEL_FREQUENCY_LOGIC:
            user_df_value = _df_to_lol(input_values[config["params"][0]])
            user_channel_type = str(input_values[config["params"][1]]).strip()
            report_headers = config["report_headers"]
            tolerance = 1e-6  # Tolerance for floating point comparisons

            # Check Dropdown (Requirement 1 & 2 indirectly relates to channel_type)
            correct_dropdown_val = str(config["correct_dropdown_value"]).strip()
            if user_channel_type != correct_dropdown_val:
                error_count += 1
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dropdown',
                    'field_label': config["dropdown_label"],
                    'user_value': user_channel_type,
                    'answer_value': correct_dropdown_val
                })

            user_downlink_start = user_downlink_end = user_uplink_start = user_uplink_end = None
            frequencies_parsed = False

            # Initial check for dataframe structure (expected to have at least one row for frequencies)
            if not isinstance(user_df_value, list) or len(user_df_value) == 0 or not all(
                    isinstance(row, list) for row in user_df_value):
                # If basic structure is wrong or empty, count as full errors for frequency fields
                error_count += 4  # 4 frequency checks (start/end downlink, start/end uplink)
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': "信道段参数表格格式错误或为空。无法解析频率数据。"
                })
            else:
                # Assuming only one row for simplicity for now, as per `channel_segment_data`
                user_row = user_df_value[0]
                expected_cols = 5  # [名称, 下行始, 下行终, 上行始, 上行终]

                if len(user_row) < expected_cols:
                    # If user row has too few columns, count errors for missing frequency fields (4 frequency fields)
                    error_count += 4
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'column_count_mismatch',
                        'row': 1,
                        'message': f"信道段参数表格第一行列数不足，应至少包含 {expected_cols} 列。",
                        'user_value': str(len(user_row)),
                        'answer_value': f"至少需要 {max_fillable_col_idx + 1} 列"
                    })
                else:
                    # Attempt to parse frequencies as floats, handling potential ValueError
                    try:
                        user_downlink_start = float(str(user_row[1]).strip())
                        user_downlink_end = float(str(user_row[2]).strip())
                        user_uplink_start = float(str(user_row[3]).strip())
                        user_uplink_end = float(str(user_row[4]).strip())
                        frequencies_parsed = True
                    except (ValueError, TypeError):
                        error_count += 4  # If any parsing fails, count all 4 frequencies as errors
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'data_type_error',
                            'message': "频率值应为数字，请检查输入。"
                        })

            if frequencies_parsed:
                # Define correct ranges and offset based on channel type
                if user_channel_type == "uu":
                    downlink_min, downlink_max = 12.25, 12.75
                    uplink_min, uplink_max = 14.0, 14.5
                    offset = 1.75
                elif user_channel_type == "aa":
                    downlink_min, downlink_max = 19.6, 21.2
                    uplink_min, uplink_max = 29.4, 31.0
                    offset = 9.8
                else:
                    # If channel type is still invalid despite dropdown check, cannot perform logical checks
                    error_count += 4  # Count 4 freq errors if type is not recognized for logic
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'logic_check_failed',
                        'message': f"无法对信道类型 '{user_channel_type}' 执行频率逻辑检查。请选择 'uu' 或 'aa'。"
                    })
                    frequencies_parsed = False  # Prevent further logical checks

                if frequencies_parsed:  # Re-check if we can proceed after type validation
                    # Requirement 1: Downlink Frequency Range
                    if not (downlink_min <= user_downlink_start <= downlink_max):
                        error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 2,
                            'col_header': report_headers[1],
                            'user_value': f"{user_downlink_start}",
                            'answer_value': f"{user_channel_type} 模式下，下行起始频率应在 {downlink_min}-{downlink_max} 范围内"
                        })
                    if not (downlink_min <= user_downlink_end <= downlink_max):
                        error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 3,
                            'col_header': report_headers[2],
                            'user_value': f"{user_downlink_end}",
                            'answer_value': f"{user_channel_type} 模式下，下行终止频率应在 {downlink_min}-{downlink_max} 范围内"
                        })

                    # Requirement 2: Uplink Frequency Range
                    if not (uplink_min <= user_uplink_start <= uplink_max):
                        error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 4,
                            'col_header': report_headers[3],
                            'user_value': f"{user_uplink_start}",
                            'answer_value': f"{user_channel_type} 模式下，上行起始频率应在 {uplink_min}-{uplink_max} 范围内"
                        })
                    if not (uplink_min <= user_uplink_end <= uplink_max):
                        error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'dataframe_cell', 'row': 1, 'col': 5,
                            'col_header': report_headers[4],
                            'user_value': f"{user_uplink_end}",
                            'answer_value': f"{user_channel_type} 模式下，上行终止频率应在 {uplink_min}-{uplink_max} 范围内"
                        })

                    # Requirement 3: Uplink-Downlink Relationship
                    if not (abs(user_uplink_start - (user_downlink_start + offset)) < tolerance):
                        error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'logic_check_failed', 'row': 1, 'col': 4,
                            'col_header': report_headers[3],
                            'user_value': f"{user_uplink_start}",
                            'answer_value': f"{user_channel_type} 模式下，上行起始频率应为 下行起始频率+{offset:.2f}"
                        })
                    if not (abs(user_uplink_end - (user_downlink_end + offset)) < tolerance):
                        error_count += 1
                        current_section_detailed_errors.append({
                            'section_title': friendly_title, 'type': 'logic_check_failed', 'row': 1, 'col': 5,
                            'col_header': report_headers[4],
                            'user_value': f"{user_uplink_end}",
                            'answer_value': f"{user_channel_type} 模式下，上行终止频率应为 下行终止频率+{offset:.2f}"
                        })

                    # NEW Requirement: Uplink_End <= Downlink_Start
                    freq_rel_err_count, freq_rel_detailed_errors = _check_uplink_downlink_frequency_rule(
                        friendly_title, 1,  # Always row 1 for this table
                        user_downlink_start, user_uplink_end,
                        report_headers[1], report_headers[4]  # Headers for Downlink Start and Uplink End
                    )
                    error_count += freq_rel_err_count
                    current_section_detailed_errors.extend(freq_rel_detailed_errors)


        elif config["check_type"] == _CHECK_TYPE_TEXTBOX_AND_DATAFRAME:
            # For "2.点对点通信参数", we no longer check exact textbox values or dataframe cells.
            # Only apply frequency rule and bandwidth-rate rule.

            user_df_value = _df_to_lol(input_values[config["params"][-1]])
            report_headers = config["report_headers"]

            # --- Textbox fields are no longer checked for exact match, but we need to ensure structure for dataframe ---
            # Original: Compare textbox values first (REMOVED)
            # user_textbox_values = [input_values[param] for param in config["params"][:-1]]
            # correct_textbox_answers = config["correct_textbox_answers"]
            # fields = config["fields"]
            # for i in range(len(correct_textbox_answers)):
            #     user_val = str(user_textbox_values[i]).strip()
            #     correct_val = str(correct_textbox_answers[i]).strip()
            #     if user_val != correct_val:
            #         error_count += 1
            #         current_section_detailed_errors.append({
            #             'section_title': friendly_title,
            #             'type': 'textbox',
            #             'field_label': fields[i],
            #             'user_value': user_val,
            #             'answer_value': correct_val
            #         })

            if not isinstance(user_df_value, list) or not all(isinstance(row, list) for row in user_df_value):
                # If malformed, count as total possible errors for this section (2 rows * 2 checks = 4 errors)
                error_count += 4
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'dataframe_format_error',
                    'message': "点对点通信参数表格格式错误或无法解析。请确保输入为有效数据。"
                })
                # No 'continue' here, as we still want to collect KBP load errors if applicable
            else:
                user_rows = len(user_df_value)
                # Assuming P2P table should always have 2 rows ("发送", "接收")
                expected_rows = 2
                if user_rows != expected_rows:
                    error_count += abs(
                        user_rows - expected_rows) * 2  # Roughly 2 errors per missing/extra row for the logic checks
                    current_section_detailed_errors.append({
                        'section_title': friendly_title,
                        'type': 'row_count_mismatch',
                        'message': f"表格行数不匹配: 您的表格有 {user_rows} 行，应有 {expected_rows} 行。",
                        'user_value': str(user_rows),
                        'answer_value': str(expected_rows)
                    })
                rows_to_compare = min(user_rows, expected_rows)

                # Identify relevant column indices for P2P table
                # _P2P_HEADERS: ["名称", "速率kbps", "带宽（khz）", "下行起始频点（khz）", "下行终止频点（khz）", "上行起始频点（khz）", "上行终止频点（khz）"]
                p2p_rate_idx = _P2P_RATE_COL_INDEX
                p2p_bandwidth_idx = _P2P_BANDWIDTH_COL_INDEX
                p2p_downlink_start_idx = _P2P_DOWNLINK_START_COL_INDEX
                p2p_uplink_end_idx = _P2P_UPLINK_END_COL_INDEX

                for r in range(rows_to_compare):
                    user_row = user_df_value[r]
                    # Check for minimum number of columns to contain all relevant data
                    min_cols_needed = max(p2p_rate_idx, p2p_bandwidth_idx, p2p_downlink_start_idx,
                                          p2p_uplink_end_idx) + 1
                    if len(user_row) < min_cols_needed:
                        error_count += 2  # Two logic checks might fail for this row
                        current_section_detailed_errors.append({
                            'section_title': friendly_title,
                            'type': 'column_count_mismatch',
                            'row': r + 1,
                            'message': f"第 {r + 1} 行列数不足，缺少必要的频率或带宽/速率列，无法进行校验。"
                        })
                        continue  # Skip logic checks for this malformed row

                    # NEW: Check for Uplink_End <= Downlink_Start for P2P table
                    dl_start_val = user_row[p2p_downlink_start_idx]
                    ul_end_val = user_row[p2p_uplink_end_idx]

                    freq_rel_err_count, freq_rel_detailed_errors = _check_uplink_downlink_frequency_rule(
                        friendly_title, r + 1,
                        dl_start_val, ul_end_val,
                        report_headers[p2p_downlink_start_idx], report_headers[p2p_uplink_end_idx]
                    )
                    error_count += freq_rel_err_count
                    current_section_detailed_errors.extend(freq_rel_detailed_errors)

                    # NEW: Check for Bandwidth >= Required Bandwidth from KBP mapping
                    user_rate_val = user_row[p2p_rate_idx]
                    user_bandwidth_val = user_row[p2p_bandwidth_idx]

                    bw_rate_err_count, bw_rate_detailed_errors = _check_bandwidth_vs_rate_rule(
                        friendly_title, r + 1,
                        user_rate_val, user_bandwidth_val,
                        report_headers[p2p_rate_idx], report_headers[p2p_bandwidth_idx]
                    )
                    error_count += bw_rate_err_count
                    current_section_detailed_errors.extend(bw_rate_detailed_errors)

            # If KBP mapping failed to load, ensure this error is reported once for the section
            # and is not already part of detailed errors from _check_bandwidth_vs_rate_rule calls
            if _KBP_LOAD_ERROR and not any(d.get('type') == 'kbp_load_error' for d in current_section_detailed_errors):
                error_count += 1  # Add one general error for KBP load failure
                current_section_detailed_errors.append({
                    'section_title': friendly_title,
                    'type': 'kbp_load_error',
                    'message': _KBP_LOAD_ERROR  # Use the global error message
                })


        else:
            print(
                f"Warning: Unsupported check type '{config['check_type']}' for section '{friendly_title}'. Cannot count errors.")
            error_count = "未知错误数"  # Indicate an internal error

        # Collect summary errors and detailed errors
        # Add section to summary only if there were errors detected or if a parsing/format error occurred.
        if error_count > 0 or (isinstance(error_count, str) and "失败" in error_count):
            if isinstance(error_count, int):
                error_sections_with_counts.append((friendly_title, error_count))
            else:
                error_sections_with_counts.append((friendly_title, error_count))

            if friendly_title not in error_titles_only:
                error_titles_only.append(friendly_title)

            detailed_errors.extend(current_section_detailed_errors)

    # Format the output message string for summary
    if not error_sections_with_counts:
        error_message_string = "恭喜，答卷全部正确！"
    else:
        error_message_string = "以下部分填写有误：\n\n"
        for title, count in error_sections_with_counts:
            if isinstance(count, int):
                error_message_string += f"- **{title}**：错误个数：{count}\n"
            else:
                error_message_string += f"- **{title}**：{count}\n"

        if detailed_errors:
            error_message_string += "\n请参考下面的**详细错误列表**查看具体差异。"

    return (error_message_string, error_sections_with_counts, error_titles_only, detailed_errors)