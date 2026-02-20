-- ============================================================================
-- OBS 毫秒级时钟脚本
-- 功能：在 OBS 中显示两行时钟
--   - 第一行：年/月/日（使用 slash.png 作为分隔符）
--   - 第二行：时:分:秒.毫秒（使用 and.png 作为分隔符）
--   - 两行居中对齐显示
-- ============================================================================

obs = obslua
bit = require("bit")

-- ============================================================================
-- 源定义配置
-- ============================================================================
source_def = {}
source_def.id = "obs_clock"
source_def.output_flags = bit.bor(obs.OBS_SOURCE_VIDEO, obs.OBS_SOURCE_CUSTOM_DRAW)

-- ============================================================================
-- 图片加载函数
-- @param image: 图片对象
-- @param file: 图片文件路径
-- 功能：加载图片文件到 OBS 纹理中
-- ============================================================================
function image_source_load(image, file)
	obs.obs_enter_graphics();
	obs.gs_image_file_free(image);
	obs.obs_leave_graphics();

	obs.gs_image_file_init(image, file);

	obs.obs_enter_graphics();
	obs.gs_image_file_init_texture(image);
	obs.obs_leave_graphics();

	if not image.loaded then
		print("请确保图片存在: " .. file);
	end
end

-- ============================================================================
-- 获取源名称
-- 返回：在 OBS 中显示的源名称
-- ============================================================================
source_def.get_name = function()
	return "日期与毫秒级时间"
end

-- ============================================================================
-- 创建源时调用
-- @param source: OBS 源对象
-- @param settings: OBS 设置对象
-- 返回：包含所有图片数据的 data 表
-- 功能：初始化所有数字图片和分隔符图片
-- ============================================================================
source_def.create = function(source, settings)
	local data = {}

	-- 初始化数字 0-9 的图片对象
	data.n0 = obs.gs_image_file()
	data.n1 = obs.gs_image_file()
	data.n2 = obs.gs_image_file()
	data.n3 = obs.gs_image_file()
	data.n4 = obs.gs_image_file()
	data.n5 = obs.gs_image_file()
	data.n6 = obs.gs_image_file()
	data.n7 = obs.gs_image_file()
	data.n8 = obs.gs_image_file()
	data.n9 = obs.gs_image_file()
	
	-- 初始化分隔符图片对象
	-- n: 用于时间分隔符（冒号）
	data.n = obs.gs_image_file()
	-- slash: 用于日期分隔符（斜杠）
	data.slash = obs.gs_image_file()
	-- slash: 用于毫秒分隔符（点）
	data.dot = obs.gs_image_file()

	-- 加载数字图片 0-9
	image_source_load(data.n0, script_path() .. "obs_clock/0.png")
	image_source_load(data.n1, script_path() .. "obs_clock/1.png")
	image_source_load(data.n2, script_path() .. "obs_clock/2.png")
	image_source_load(data.n3, script_path() .. "obs_clock/3.png")
	image_source_load(data.n4, script_path() .. "obs_clock/4.png")
	image_source_load(data.n5, script_path() .. "obs_clock/5.png")
	image_source_load(data.n6, script_path() .. "obs_clock/6.png")
	image_source_load(data.n7, script_path() .. "obs_clock/7.png")
	image_source_load(data.n8, script_path() .. "obs_clock/8.png")
	image_source_load(data.n9, script_path() .. "obs_clock/9.png")
	
	-- 加载分隔符图片
	image_source_load(data.n, script_path() .. "obs_clock/and.png")
	image_source_load(data.slash, script_path() .. "obs_clock/slash.png")
	image_source_load(data.dot, script_path() .. "obs_clock/dot.png")

	return data
end

-- ============================================================================
-- 销毁源时调用
-- @param data: 源数据对象
-- 功能：释放所有图片资源
-- ============================================================================
source_def.destroy = function(data)
	obs.obs_enter_graphics();
	
	-- 释放数字图片资源
	obs.gs_image_file_free(data.n0);
	obs.gs_image_file_free(data.n1);
	obs.gs_image_file_free(data.n2);
	obs.gs_image_file_free(data.n3);
	obs.gs_image_file_free(data.n4);
	obs.gs_image_file_free(data.n5);
	obs.gs_image_file_free(data.n6);
	obs.gs_image_file_free(data.n7);
	obs.gs_image_file_free(data.n8);
	obs.gs_image_file_free(data.n9);
	
	-- 释放分隔符图片资源
	obs.gs_image_file_free(data.n);
	obs.gs_image_file_free(data.slash);
	obs.gs_image_file_free(data.dot);

	obs.obs_leave_graphics();
end

-- ============================================================================
-- 视频渲染函数
-- @param data: 源数据对象
-- @param effect: OBS 效果对象
-- 功能：每帧渲染时钟显示
-- 布局说明：
--   - 第一行（Y=0）：年/月/日，格式 YYYY/MM/DD，共 10 个字符
--   - 第二行（Y=30）：时:分:秒.毫秒，格式 HH:MM:SS.mmm，共 12 个字符
--   - 每个字符宽度为 22 像素
--   - 两行居中对齐
-- ============================================================================
source_def.video_render = function(data, effect)
	if not data.n.texture then
		return;
	end
	
	-- 获取当前时间
	local time = os.date("*t")
	
	-- 获取毫秒数（从 os.clock() 中提取小数部分）
	-- 注意：os.clock() 返回程序运行的 CPU 时间，格式如 "0.123456"
	-- 使用 string.match 提取小数部分，如果匹配失败则使用默认值 "000"
	local ms = string.match(tostring(os.clock()), "%d%.(%d+)")
	if not ms or string.len(ms) < 3 then
		ms = "000"  -- 默认值，防止 nil 错误
	else
		-- 只取前3位毫秒
		ms = string.sub(ms, 1, 3)
	end
	
	-- 格式化时间各部分，确保两位数显示
	local hours = AddZeroFrontNum(2, time.hour)
	local mins = AddZeroFrontNum(2, time.min)
	local seconds = AddZeroFrontNum(2, time.sec)
	
	-- 格式化日期各部分
	-- 年份：4位数
	local year = tostring(time.year)
	-- 月份和日期：确保两位数显示
	local month = AddZeroFrontNum(2, time.month)
	local day = AddZeroFrontNum(2, time.day)

	effect = obs.obs_get_base_effect(obs.OBS_EFFECT_DEFAULT)

	obs.gs_blend_state_push()
	obs.gs_reset_blend_state()

	while obs.gs_effect_loop(effect, "Draw") do
		
		-- ====================================================================
		-- 第一行：显示 年/月/日
		-- 格式：YYYY/MM/DD（共 10 个字符，宽度 220 像素）
		-- 居中对齐：起始 X = (264 - 220) / 2 = 22
		-- ====================================================================
		local line1_start_x = 22
		local line1_y = 0
		local char_width = 22  -- 每个字符宽度
		
		-- 显示年份（4位数字）
		-- 年份第1位
		obs.obs_source_draw(get_number(data, string.sub(year, 1, 1)), line1_start_x + 0 * char_width, line1_y, 0, 0, false);
		-- 年份第2位
		obs.obs_source_draw(get_number(data, string.sub(year, 2, 2)), line1_start_x + 1 * char_width, line1_y, 0, 0, false);
		-- 年份第3位
		obs.obs_source_draw(get_number(data, string.sub(year, 3, 3)), line1_start_x + 2 * char_width, line1_y, 0, 0, false);
		-- 年份第4位
		obs.obs_source_draw(get_number(data, string.sub(year, 4, 4)), line1_start_x + 3 * char_width, line1_y, 0, 0, false);
		-- 斜杠分隔符
		obs.obs_source_draw(data.slash.texture, line1_start_x + 4 * char_width, line1_y, 0, 0, false);
		
		-- 显示月份（2位数字）
		obs.obs_source_draw(get_number(data, string.sub(month, 1, 1)), line1_start_x + 5 * char_width, line1_y, 0, 0, false);
		obs.obs_source_draw(get_number(data, string.sub(month, 2, 2)), line1_start_x + 6 * char_width, line1_y, 0, 0, false);
		-- 斜杠分隔符
		obs.obs_source_draw(data.slash.texture, line1_start_x + 7 * char_width, line1_y, 0, 0, false);
		
		-- 显示日期（2位数字）
		obs.obs_source_draw(get_number(data, string.sub(day, 1, 1)), line1_start_x + 8 * char_width, line1_y, 0, 0, false);
		obs.obs_source_draw(get_number(data, string.sub(day, 2, 2)), line1_start_x + 9 * char_width, line1_y, 0, 0, false);

		-- ====================================================================
		-- 第二行：显示 时:分:秒.毫秒
		-- 格式：HH:MM:SS.mmm（共 12 个字符，宽度 264 像素）
		-- 居中对齐：起始 X = (264 - 264) / 2 = 0
		-- ====================================================================
		local line2_start_x = 0
		local line2_y = 30  -- 第二行 Y 坐标，在第一行下方 30 像素
		
		-- 显示小时（2位数字）
		obs.obs_source_draw(get_number(data, string.sub(hours, 1, 1)), line2_start_x + 0 * char_width, line2_y, 0, 0, false);
		obs.obs_source_draw(get_number(data, string.sub(hours, 2, 2)), line2_start_x + 1 * char_width, line2_y, 0, 0, false);
		-- 冒号分隔符
		obs.obs_source_draw(data.n.texture, line2_start_x + 2 * char_width, line2_y, 0, 0, false);

		-- 显示分钟（2位数字）
		obs.obs_source_draw(get_number(data, string.sub(mins, 1, 1)), line2_start_x + 3 * char_width, line2_y, 0, 0, false);
		obs.obs_source_draw(get_number(data, string.sub(mins, 2, 2)), line2_start_x + 4 * char_width, line2_y, 0, 0, false);
		-- 冒号分隔符
		obs.obs_source_draw(data.n.texture, line2_start_x + 5 * char_width, line2_y, 0, 0, false);

		-- 显示秒（2位数字）
		obs.obs_source_draw(get_number(data, string.sub(seconds, 1, 1)), line2_start_x + 6 * char_width, line2_y, 0, 0, false);
		obs.obs_source_draw(get_number(data, string.sub(seconds, 2, 2)), line2_start_x + 7 * char_width, line2_y, 0, 0, false);
		-- 小数点分隔符
		obs.obs_source_draw(data.dot.texture, line2_start_x + 8 * char_width, line2_y, 0, 0, false);

		-- 显示毫秒（3位数字）
		obs.obs_source_draw(get_number(data, string.sub(ms, 1, 1)), line2_start_x + 9 * char_width, line2_y, 0, 0, false);
		obs.obs_source_draw(get_number(data, string.sub(ms, 2, 2)), line2_start_x + 10 * char_width, line2_y, 0, 0, false);
		obs.obs_source_draw(get_number(data, string.sub(ms, 3, 3)), line2_start_x + 11 * char_width, line2_y, 0, 0, false);

	end

	obs.gs_blend_state_pop()
end

-- ============================================================================
-- 计算数字位数
-- @param num: 要计算的数字
-- 返回：数字的位数，如果输入无效返回 -1
-- 功能：计算一个非负整数的位数
-- ============================================================================
function DightNum(num)
    if math.floor(num) ~= num or num < 0 then
        return -1
    elseif 0 == num then
        return 1
    else
        local tmp_dight = 0
        while num > 0 do
            num = math.floor(num/10)
            tmp_dight = tmp_dight + 1
        end
        return tmp_dight 
    end
end

-- ============================================================================
-- 在数字前补零
-- @param dest_dight: 目标位数
-- @param num: 要处理的数字
-- 返回：补零后的字符串
-- 功能：将数字转换为指定位数的字符串，不足位数在前面补零
-- 例如：AddZeroFrontNum(2, 5) 返回 "05"
-- ============================================================================
function AddZeroFrontNum(dest_dight, num)
    local num_dight = DightNum(num)
    if -1 == num_dight then
        -- 如果输入无效，返回由 "0" 组成的字符串，避免后续 string.sub 出错
        local str_e = ""
        for var = 1, dest_dight do
            str_e = str_e .. "0"
        end
        return str_e
    elseif num_dight >= dest_dight then
        return tostring(num)
    else
        local str_e = ""
        for var = 1, dest_dight - num_dight do
            str_e = str_e .. "0"
        end
        return str_e .. tostring(num)
    end
end


-- ============================================================================
-- 获取数字对应的纹理
-- @param data: 源数据对象
-- @param n: 数字字符（'0'-'9'）
-- 返回：对应数字的纹理对象
-- 功能：根据数字字符返回对应的图片纹理
-- ============================================================================
function get_number(data, n)
	local t = data.n0.texture
	if n == '0' then
		t = data.n0.texture
	elseif n == '1' then
		t = data.n1.texture
	elseif n == '2' then
		t = data.n2.texture
	elseif n == '3' then
		t = data.n3.texture
	elseif n == '4' then
		t = data.n4.texture
	elseif n == '5' then
		t = data.n5.texture
	elseif n == '6' then
		t = data.n6.texture
	elseif n == '7' then
		t = data.n7.texture
	elseif n == '8' then
		t = data.n8.texture
	elseif n == '9' then
		t = data.n9.texture
	end
	return t
end

-- ============================================================================
-- 获取源宽度
-- 返回：源的宽度（像素）
-- 说明：第二行（时:分:秒.毫秒）较宽，共 12 个字符 × 22 像素 = 264 像素
-- ============================================================================
source_def.get_width = function(data)
	return 264
end

-- ============================================================================
-- 获取源高度
-- 返回：源的高度（像素）
-- 说明：两行显示，每行 30 像素，共 60 像素
-- ============================================================================
source_def.get_height = function(data)
	return 60
end

-- ============================================================================
-- 脚本描述
-- 返回：脚本的描述信息
-- ============================================================================
function script_description()
	return "OBS 毫秒级时钟 - 两行显示（年/月/日 + 时:分:秒.毫秒）"
end

-- ============================================================================
-- 注册 OBS 源
-- ============================================================================
obs.obs_register_source(source_def)
