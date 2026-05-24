-- ============================================================
-- Prompt 工厂基座 - 数据库初始化脚本
-- 数据库: PostgreSQL 16 + pgvector
-- 说明: 包含建库、建表、索引、约束及中文注释，全部使用 IF NOT EXISTS 幂等执行
-- 用法:
--   方式一（psql -f 方式，自动建库+建表）:
--     psql -U postgres -f init.sql
--   方式二（docker exec 管道方式）:
--     cat init.sql | docker exec -i pgvector16 psql -U linyi -d edureport
--   注意：此脚本不使用 \gexec 和 \connect 等 psql 元命令，
--         兼容 docker exec -i 管道输入
-- ============================================================

-- ============================================================
-- 第一部分：创建数据库和用户（需连接到 postgres 库执行）
-- 如果已通过 docker-compose 或手动创建过数据库，可跳过此部分
-- ============================================================

-- 创建用户（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pf_user') THEN
        CREATE ROLE pf_user WITH LOGIN PASSWORD 'prompt_factory_2026';
        RAISE NOTICE '已创建用户 pf_user';
    ELSE
        RAISE NOTICE '用户 pf_user 已存在，跳过创建';
    END IF;
END
$$;

-- 创建数据库（如果不存在）
-- 使用 DO 块 + dblink 替代 \gexec，兼容管道输入
-- 如果 dblink 不可用则跳过，手动创建即可
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'prompt_factory') THEN
        PERFORM dblink_exec('dbname=postgres', 'CREATE DATABASE prompt_factory OWNER pf_user ENCODING ''UTF8''');
        RAISE NOTICE '已创建数据库 prompt_factory';
    ELSE
        RAISE NOTICE '数据库 prompt_factory 已存在，跳过创建';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '自动建库失败（%），请手动执行: CREATE DATABASE prompt_factory OWNER pf_user;', SQLERRM;
END
$$;

-- 授予用户权限
DO $$
BEGIN
    PERFORM 1 FROM pg_database WHERE datname = 'prompt_factory';
    IF FOUND THEN
        EXECUTE 'GRANT ALL PRIVILEGES ON DATABASE prompt_factory TO pf_user';
        RAISE NOTICE '已授予 pf_user 对数据库 prompt_factory 的全部权限';
    END IF;
END
$$;

-- ============================================================
-- 第二部分：创建扩展和表
-- 以下语句在当前连接的数据库中执行
-- 如果需要建到 prompt_factory 库，请先 \c prompt_factory 或
-- 使用 psql -d prompt_factory 连接后再执行
-- ============================================================

-- 启用 pgvector 扩展（向量存储，用于 Prompt 去重相似度检索）
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. 项目表
-- 存储评测项目的基本信息和配置
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id          VARCHAR(64)  PRIMARY KEY,        -- 项目唯一标识，由调用方指定或自动生成
    name        VARCHAR(200) NOT NULL,            -- 项目名称
    description TEXT         DEFAULT '',           -- 项目描述
    config      JSONB        DEFAULT '{}',         -- 项目级配置（相似度阈值、默认人设等级等）
    created_at  TIMESTAMPTZ  DEFAULT NOW(),        -- 创建时间
    updated_at  TIMESTAMPTZ  DEFAULT NOW()         -- 更新时间
);

COMMENT ON TABLE  projects            IS '项目表 - 管理评测项目的基本信息和配置';
COMMENT ON COLUMN projects.id         IS '项目唯一标识，支持字母/数字/下划线/短横线，最长64字符';
COMMENT ON COLUMN projects.name       IS '项目名称';
COMMENT ON COLUMN projects.description IS '项目描述';
COMMENT ON COLUMN projects.config     IS '项目级配置JSON，可包含 similarity_threshold、human_likeness、source_models 等覆盖全局默认值';
COMMENT ON COLUMN projects.created_at IS '创建时间';
COMMENT ON COLUMN projects.updated_at IS '最后更新时间';

-- ============================================================
-- 2. 人格特征表
-- 存储人设维度的可选值，支持公共/项目两级继承覆盖
-- ============================================================
CREATE TABLE IF NOT EXISTS persona_traits (
    id          SERIAL       PRIMARY KEY,         -- 自增主键
    category    VARCHAR(50)  NOT NULL,             -- 特征分类：occupation/mood/language_habit/typing_habit/scene/education
    label       VARCHAR(200) NOT NULL,             -- 特征标签值，如"程序员"、"焦虑"
    traits      JSONB        DEFAULT '[]',         -- 特征详细属性列表
    weight      FLOAT        DEFAULT 1.0,          -- 加权随机采样权重，值越大被选中概率越高
    scope       VARCHAR(20)  NOT NULL DEFAULT 'public',  -- 作用域：public=公共资源，project=项目专属
    project_id  VARCHAR(64)  REFERENCES projects(id) ON DELETE CASCADE,  -- 关联项目ID，scope=project时必填
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW(),

    CONSTRAINT ck_persona_traits_scope CHECK (scope IN ('public', 'project'))
);

COMMENT ON TABLE  persona_traits              IS '人格特征表 - 存储人设维度的可选值，支持公共/项目两级继承';
COMMENT ON COLUMN persona_traits.id           IS '自增主键';
COMMENT ON COLUMN persona_traits.category     IS '特征分类：occupation(职业)/mood(情绪)/language_habit(语言习惯)/typing_habit(打字习惯)/scene(场景)/education(教育)';
COMMENT ON COLUMN persona_traits.label        IS '特征标签值，如"程序员"、"焦虑"、"口语化"';
COMMENT ON COLUMN persona_traits.traits       IS '特征详细属性列表JSON，可包含该标签的子属性';
COMMENT ON COLUMN persona_traits.weight       IS '加权随机采样权重，值越大被选中概率越高，默认1.0';
COMMENT ON COLUMN persona_traits.scope        IS '作用域：public=公共资源(所有项目共享)，project=项目专属(仅指定项目可见)';
COMMENT ON COLUMN persona_traits.project_id   IS '关联项目ID，scope=project时必填；scope=public时为NULL';

-- 索引：按分类查询
CREATE INDEX IF NOT EXISTS ix_persona_traits_category ON persona_traits (category);
-- 索引：按作用域+项目查询
CREATE INDEX IF NOT EXISTS ix_persona_traits_scope_project ON persona_traits (scope, project_id);
-- 部分索引：仅索引项目级记录，公共级不占索引空间
CREATE INDEX IF NOT EXISTS ix_persona_traits_project_scope_project ON persona_traits (project_id) WHERE scope = 'project';

-- ============================================================
-- 3. Prompt 表
-- 存储生成的 Prompt 及其向量嵌入，用于去重检索
-- ============================================================
CREATE TABLE IF NOT EXISTS prompts (
    id              VARCHAR(36)  PRIMARY KEY,      -- UUID 格式的 Prompt 唯一标识
    project_id      VARCHAR(64)  NOT NULL REFERENCES projects(id) ON DELETE CASCADE,  -- 所属项目
    text            TEXT         NOT NULL,          -- 生成的 Prompt 文本内容
    embedding       vector(1536),                   -- 文本向量嵌入（pgvector），用于余弦相似度去重
    persona_snapshot JSONB        DEFAULT '{}',      -- 生成时使用的人设快照（保留生成上下文）
    source_model    VARCHAR(50),                    -- 生成使用的模型名称
    dedup_skipped   BOOLEAN      DEFAULT FALSE,     -- 是否跳过去重检查（Embedding API 不可用时为 TRUE）
    task_domain     VARCHAR(200),                   -- 任务领域，如"医疗咨询"、"技术问答"
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

COMMENT ON TABLE  prompts                 IS 'Prompt表 - 存储生成的Prompt及其向量嵌入，支持去重检索';
COMMENT ON COLUMN prompts.id              IS 'Prompt唯一标识，UUID格式';
COMMENT ON COLUMN prompts.project_id      IS '所属项目ID';
COMMENT ON COLUMN prompts.text            IS '生成的Prompt文本内容';
COMMENT ON COLUMN prompts.embedding       IS '文本向量嵌入(1536维)，使用pgvector存储，用于余弦相似度去重检索';
COMMENT ON COLUMN prompts.persona_snapshot IS '生成时使用的人设快照JSON，记录当时的职业/情绪/语言习惯等，便于溯源';
COMMENT ON COLUMN prompts.source_model    IS '生成使用的模型配置名称，如 deepseek-chat、gpt-4o-mini';
COMMENT ON COLUMN prompts.dedup_skipped   IS '是否跳过去重检查，当Embedding API不可用时设为TRUE，避免阻塞生成流程';
COMMENT ON COLUMN prompts.task_domain     IS '任务领域，如"医疗咨询"、"技术问答"、"日常闲聊"';
COMMENT ON COLUMN prompts.created_at      IS '生成时间';

-- 索引：按项目查询
CREATE INDEX IF NOT EXISTS ix_prompts_project_id ON prompts (project_id);
-- 索引：按项目+时间倒序查询（历史记录分页）
CREATE INDEX IF NOT EXISTS ix_prompts_project_created ON prompts (project_id, created_at DESC);

-- ============================================================
-- 4. 元提示模板表
-- 存储生成 Prompt 的 system prompt 模板，支持变量插值
-- ============================================================
CREATE TABLE IF NOT EXISTS meta_prompt_templates (
    id          SERIAL       PRIMARY KEY,
    template    TEXT         NOT NULL,              -- 模板文本，支持 {{role}}/{{scene}}/{{mood}}/{{quirk}}/{{domain}}/{{descriptions}} 变量插值
    scope       VARCHAR(20)  NOT NULL DEFAULT 'public',
    project_id  VARCHAR(64)  REFERENCES projects(id) ON DELETE CASCADE,
    enabled     BOOLEAN      DEFAULT TRUE,          -- 是否启用，禁用后不参与模板选择
    weight      FLOAT        DEFAULT 1.0,           -- 加权随机选择权重
    created_at  TIMESTAMPTZ  DEFAULT NOW(),

    CONSTRAINT ck_meta_prompt_templates_scope CHECK (scope IN ('public', 'project'))
);

COMMENT ON TABLE  meta_prompt_templates              IS '元提示模板表 - 存储生成Prompt的system prompt模板';
COMMENT ON COLUMN meta_prompt_templates.id           IS '自增主键';
COMMENT ON COLUMN meta_prompt_templates.template     IS '模板文本，支持 {{role}}/{{scene}}/{{mood}}/{{quirk}}/{{domain}}/{{descriptions}} 变量插值';
COMMENT ON COLUMN meta_prompt_templates.scope        IS '作用域：public=公共模板，project=项目专属模板';
COMMENT ON COLUMN meta_prompt_templates.project_id   IS '关联项目ID，scope=project时必填';
COMMENT ON COLUMN meta_prompt_templates.enabled      IS '是否启用，禁用后不参与模板的加权随机选择';
COMMENT ON COLUMN meta_prompt_templates.weight       IS '加权随机选择权重，值越大被选中概率越高';
COMMENT ON COLUMN meta_prompt_templates.created_at   IS '创建时间';

-- ============================================================
-- 5. 后处理规则表
-- 存储对 LLM 生成文本的后处理变换规则，模拟人类打字习惯
-- ============================================================
CREATE TABLE IF NOT EXISTS postprocess_rules (
    id          SERIAL       PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,       -- 规则名称，如 prefix_filler、replace_de、randomize_punctuation
    description TEXT         DEFAULT '',             -- 规则描述
    probability FLOAT        NOT NULL DEFAULT 0.1,   -- 触发概率(0~1)，实际概率 = probability × human_likeness倍率
    params      JSONB        DEFAULT '{}',           -- 规则参数JSON，不同规则有不同参数
    scope       VARCHAR(20)  NOT NULL DEFAULT 'public',
    project_id  VARCHAR(64)  REFERENCES projects(id) ON DELETE CASCADE,
    enabled     BOOLEAN      DEFAULT TRUE,
    sort_order  INT          NOT NULL DEFAULT 0,     -- 执行顺序，数值越小越先执行
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW(),

    CONSTRAINT ck_postprocess_rules_scope CHECK (scope IN ('public', 'project'))
);

COMMENT ON TABLE  postprocess_rules              IS '后处理规则表 - 存储对LLM生成文本的后处理变换规则，模拟人类打字习惯';
COMMENT ON COLUMN postprocess_rules.id           IS '自增主键';
COMMENT ON COLUMN postprocess_rules.name         IS '规则唯一名称：prefix_filler/replace_de/randomize_punctuation/insert_filler_words/lowercase_start/mess_spacing/remove_punctuation';
COMMENT ON COLUMN postprocess_rules.description  IS '规则功能描述';
COMMENT ON COLUMN postprocess_rules.probability   IS '触发概率(0~1)，实际执行概率 = probability × human_likeness倍率，上限1.0';
COMMENT ON COLUMN postprocess_rules.params       IS '规则参数JSON，如 {"fillers": ["嗯", "啊"]}, {"probability": 0.3}';
COMMENT ON COLUMN postprocess_rules.scope        IS '作用域：public=公共规则，project=项目专属规则';
COMMENT ON COLUMN postprocess_rules.project_id   IS '关联项目ID，scope=project时必填';
COMMENT ON COLUMN postprocess_rules.enabled      IS '是否启用';
COMMENT ON COLUMN postprocess_rules.sort_order   IS '执行顺序，数值越小越先执行，相同sort_order按created_at排序';

-- 索引：按作用域+项目查询
CREATE INDEX IF NOT EXISTS ix_postprocess_rules_scope_project ON postprocess_rules (scope, project_id);

-- ============================================================
-- 6. 模型配置表
-- 存储可用的 LLM 模型配置，支持 4 种 Provider 类型和公共/项目两级继承
-- API Key 通过前端填写，使用 Fernet 对称加密后存储于 api_key_encrypted 字段
-- ============================================================
CREATE TABLE IF NOT EXISTS model_configs (
    id               SERIAL       PRIMARY KEY,
    name             VARCHAR(50)  NOT NULL UNIQUE,     -- 模型配置名称，如 deepseek-chat、claude-3-5-sonnet
    provider_type    VARCHAR(20)  NOT NULL DEFAULT 'openai',  -- Provider类型：openai/anthropic/azure/bedrock
    api_key_encrypted TEXT,                              -- Fernet加密后的API Key密文，通过前端管理页面填写
    base_url         VARCHAR(500) NOT NULL,             -- API 基础URL
    model_name       VARCHAR(100) NOT NULL,             -- 实际模型标识，如 gpt-4o-mini、claude-3-5-sonnet-20241022
    weight           FLOAT        DEFAULT 1.0,          -- 加权随机选择权重
    max_tokens       INT          DEFAULT 256,          -- 单次生成最大Token数
    timeout          INT          DEFAULT 30,           -- 请求超时时间(秒)
    scope            VARCHAR(20)  NOT NULL DEFAULT 'public',
    project_id       VARCHAR(64)  REFERENCES projects(id) ON DELETE CASCADE,
    enabled          BOOLEAN      DEFAULT TRUE,
    created_at       TIMESTAMPTZ  DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  DEFAULT NOW(),

    CONSTRAINT ck_model_configs_scope CHECK (scope IN ('public', 'project')),
    CONSTRAINT ck_model_configs_provider_type CHECK (provider_type IN ('openai', 'anthropic', 'azure', 'bedrock'))
);

COMMENT ON TABLE  model_configs                    IS '模型配置表 - 存储可用的LLM模型配置，API Key通过前端填写并加密存储';
COMMENT ON COLUMN model_configs.id                 IS '自增主键';
COMMENT ON COLUMN model_configs.name               IS '模型配置唯一名称，如 deepseek-chat、claude-3-5-sonnet、azure-gpt-4o-mini';
COMMENT ON COLUMN model_configs.provider_type      IS 'Provider类型：openai=OpenAI兼容接口(覆盖大部分厂商)/anthropic=Anthropic原生API/azure=Azure OpenAI/bedrock=Amazon Bedrock';
COMMENT ON COLUMN model_configs.api_key_encrypted  IS 'Fernet对称加密后的API Key密文，通过前端管理页面填写明文Key后由后端加密存储，解密密钥由SECRET_KEY配置项派生';
COMMENT ON COLUMN model_configs.base_url           IS 'API基础URL，如 https://api.openai.com/v1、https://api.anthropic.com';
COMMENT ON COLUMN model_configs.model_name         IS '实际模型标识，如 gpt-4o-mini、claude-3-5-sonnet-20241022、moonshot-v1-8k';
COMMENT ON COLUMN model_configs.weight             IS '加权随机选择权重，值越大被选中概率越高';
COMMENT ON COLUMN model_configs.max_tokens         IS '单次生成最大Token数，默认256';
COMMENT ON COLUMN model_configs.timeout            IS '请求超时时间(秒)，默认30';
COMMENT ON COLUMN model_configs.scope              IS '作用域：public=公共模型(所有项目可用)，project=项目专属模型';
COMMENT ON COLUMN model_configs.project_id         IS '关联项目ID，scope=project时必填';
COMMENT ON COLUMN model_configs.enabled            IS '是否启用，禁用后不参与模型选择';

-- ============================================================
-- 第三部分：种子数据初始化
-- 使用 DO $$ 块包裹，仅在表为空时插入，保证幂等
-- ============================================================

-- ============================================================
-- 3.1 人格特征种子数据（persona_traits）
-- 数据来源：persona_bank.yaml，共 101 条，6 个分类
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM persona_traits LIMIT 1) THEN
        INSERT INTO persona_traits (category, label, traits, weight, scope) VALUES
        -- ---- occupation（职业）24条 ----
        ('occupation', '外卖骑手',   '["赶时间", "路线熟", "怕差评", "手机不离手", "风里来雨里去"]', 1.2, 'public'),
        ('occupation', '全职宝妈',   '["关注育儿", "精打细算", "社交圈子以家长群为主", "时间碎片化", "关注健康"]', 1.1, 'public'),
        ('occupation', '实习护士',   '["值夜班", "手忙脚乱", "被前辈使唤", "心疼病人", "学习心切"]', 0.9, 'public'),
        ('occupation', '退休教师',   '["爱说教", "关注教育政策", "生活规律", "喜欢回忆过去", "关心学生"]', 0.8, 'public'),
        ('occupation', '程序员',     '["逻辑思维强", "久坐", "咖啡续命", "社恐", "关注技术动态"]', 1.3, 'public'),
        ('occupation', '大学生',     '["时间自由", "追热点", "社交活跃", "经济紧张", "对未来迷茫"]', 1.2, 'public'),
        ('occupation', '出租车司机', '["健谈", "路怒", "久坐腰不好", "听广播", "对城市了如指掌"]', 1.0, 'public'),
        ('occupation', '小店老板',   '["精明", "起早贪黑", "人情世故", "算账快", "看人准"]', 0.9, 'public'),
        ('occupation', '快递员',     '["风风火火", "怕丢件", "手机响不停", "体力活", "客户是上帝"]', 1.0, 'public'),
        ('occupation', '建筑工人',   '["体力好", "话少", "想家", "工友之间互相帮衬", "关注工资发放"]', 0.8, 'public'),
        ('occupation', '厨师',       '["对食材挑剔", "烫伤是家常便饭", "烟熏火燎", "吃饭不规律", "讲究火候"]', 0.8, 'public'),
        ('occupation', '保安',       '["无聊", "夜班多", "认真负责", "爱管闲事", "关注小区动态"]', 0.7, 'public'),
        ('occupation', '保洁阿姨',   '["勤劳", "怕被嫌弃", "话不多", "关注卫生", "节省"]', 0.7, 'public'),
        ('occupation', '销售经理',   '["能说会道", "应酬多", "业绩压力大", "人脉广", "关注市场动态"]', 1.0, 'public'),
        ('occupation', '会计',       '["细心", "怕出错", "月底忙", "对数字敏感", "规矩意识强"]', 0.9, 'public'),
        ('occupation', '律师',       '["逻辑严密", "措辞谨慎", "工作强度大", "关注法律更新", "好辩"]', 0.8, 'public'),
        ('occupation', '医生',       '["忙碌", "专业权威", "见惯生死", "值夜班", "对患者有耐心"]', 0.9, 'public'),
        ('occupation', '药师',       '["严谨", "对药物敏感", "关注用药安全", "工作重复性高", "细心"]', 0.7, 'public'),
        ('occupation', '自由职业者', '["时间自由", "收入不稳定", "自律要求高", "社交少", "焦虑与自由并存"]', 1.0, 'public'),
        ('occupation', '网约车司机', '["看导航", "接单焦虑", "久坐", "车内环境讲究", "对平台规则敏感"]', 1.0, 'public'),
        ('occupation', '房产中介',   '["热情", "嘴甜", "对房价敏感", "带看辛苦", "业绩驱动"]', 0.8, 'public'),
        ('occupation', '餐厅服务员', '["笑脸迎人", "脚酸", "记菜单", "怕投诉", "忙时脚不沾地"]', 0.8, 'public'),
        ('occupation', '工厂工人',   '["重复劳动", "倒班", "想加班多赚", "工友关系简单", "关注工资"]', 0.8, 'public'),
        ('occupation', '外卖小哥',   '["争分夺秒", "怕超时", "风雨无阻", "手机导航", "客户评价敏感"]', 1.1, 'public'),
        ('occupation', '网络主播',   '["镜头感强", "话多", "关注流量", "互动频繁", "作息颠倒"]', 0.9, 'public'),

        -- ---- mood（情绪）20条 ----
        ('mood', '焦虑',   '["坐立不安", "反复确认", "语速快", "注意力难集中", "容易出汗"]', 1.2, 'public'),
        ('mood', '急躁',   '["不耐烦", "打断别人", "催促", "语气冲", "坐不住"]', 1.1, 'public'),
        ('mood', '平静',   '["语气平和", "有条不紊", "不急不躁", "理性思考", "从容"]', 1.0, 'public'),
        ('mood', '好奇',   '["追问", "探索欲强", "关注细节", "喜欢新事物", "眼睛发亮"]', 1.0, 'public'),
        ('mood', '烦躁',   '["叹气", "来回走动", "对小事发火", "不想说话", "心神不宁"]', 1.1, 'public'),
        ('mood', '无奈',   '["叹气", "摇头", "语气低沉", "放弃争辩", "认命"]', 1.0, 'public'),
        ('mood', '兴奋',   '["语速快", "手舞足蹈", "声音高亢", "停不下来", "分享欲强"]', 1.0, 'public'),
        ('mood', '疲惫',   '["反应慢", "不想动", "说话有气无力", "想睡觉", "眼神涣散"]', 1.1, 'public'),
        ('mood', '放松',   '["语速慢", "随意", "不拘小节", "享受当下", "笑容多"]', 0.9, 'public'),
        ('mood', '紧张',   '["手心出汗", "结巴", "反复确认", "不敢对视", "心跳加速"]', 1.0, 'public'),
        ('mood', '开心',   '["笑容满面", "话多", "乐于分享", "精力充沛", "看什么都顺眼"]', 1.0, 'public'),
        ('mood', '沮丧',   '["沉默", "不想社交", "自我否定", "提不起劲", "回避目光"]', 0.9, 'public'),
        ('mood', '期待',   '["频繁看手机", "计划未来", "语气上扬", "坐不住", "想象美好结果"]', 0.9, 'public'),
        ('mood', '委屈',   '["眼眶泛红", "声音哽咽", "想解释又说不出口", "低头", "咬嘴唇"]', 0.8, 'public'),
        ('mood', '愤怒',   '["声音大", "拍桌子", "呼吸急促", "语言攻击", "脸红"]', 1.0, 'public'),
        ('mood', '满足',   '["微笑", "感恩", "知足", "语气温柔", "享受当下"]', 0.8, 'public'),
        ('mood', '迷茫',   '["发呆", "不知道说什么", "反复问为什么", "犹豫不决", "眼神空洞"]', 1.0, 'public'),
        ('mood', '感动',   '["眼眶湿润", "声音颤抖", "想表达感谢", "沉默片刻", "心里暖暖的"]', 0.7, 'public'),
        ('mood', '孤独',   '["自言自语", "刷手机", "不想出门", "渴望被理解", "沉默寡言"]', 0.9, 'public'),
        ('mood', '骄傲',   '["挺胸抬头", "语气自信", "喜欢被夸", "不愿认错", "展示成就"]', 0.7, 'public'),

        -- ---- language_habit（语言习惯）20条 ----
        ('language_habit', '口语化',       '["用词简单", "短句多", "语气词多", "不讲究语法", "像聊天"]', 1.3, 'public'),
        ('language_habit', '书面语',       '["用词正式", "句式完整", "少语气词", "逻辑清晰", "像写文章"]', 0.8, 'public'),
        ('language_habit', '网络用语多',   '["用梗", "缩写", "表情包文字化", "追热点词", "yyds/绝绝子"]', 1.2, 'public'),
        ('language_habit', '方言味重',     '["方言词汇", "语序特殊", "声调不同", "俚语多", "普通话不标准"]', 1.0, 'public'),
        ('language_habit', '喜欢用缩写',   '["xswl", "zqsg", "u1s1", "kdl", "首字母代替"]', 0.9, 'public'),
        ('language_habit', '爱说口头禅',   '["然后", "就是说", "你知道吗", "对吧", "反正"]', 1.1, 'public'),
        ('language_habit', '说话简洁',     '["惜字如金", "不废话", "直奔主题", "短句", "不解释"]', 1.0, 'public'),
        ('language_habit', '说话啰嗦',     '["绕弯子", "重复", "铺垫长", "细节多", "说了半天没到重点"]', 0.9, 'public'),
        ('language_habit', '喜欢用比喻',   '["打比方", "形象化", "类比", "画面感强", "生动"]', 0.8, 'public'),
        ('language_habit', '爱用反问句',   '["难道不是吗", "你想想", "这不是明摆着吗", "谁不知道啊", "不是吧"]', 0.9, 'public'),
        ('language_habit', '语气词多',     '["啊", "呢", "吧", "嘛", "哦"]', 1.2, 'public'),
        ('language_habit', '喜欢引经据典', '["引用名言", "古文", "成语", "典故", "掉书袋"]', 0.6, 'public'),
        ('language_habit', '中英夹杂',     '["混用英文", "presentation", "meeting", "deadline", "职场腔"]', 0.8, 'public'),
        ('language_habit', '爱用叠词',     '["慢慢来", "轻轻的", "小小的", "热热的", "软软的"]', 0.7, 'public'),
        ('language_habit', '说话直白',     '["不绕弯", "有什么说什么", "不修饰", "可能伤人", "效率高"]', 1.0, 'public'),
        ('language_habit', '委婉含蓄',     '["暗示", "不直说", "留余地", "话里有话", "顾及面子"]', 0.8, 'public'),
        ('language_habit', '喜欢用感叹号', '["情绪外露", "强调", "激动", "每句都感叹", "热情"]', 1.0, 'public'),
        ('language_habit', '爱用省略号',   '["欲言又止", "意味深长", "留白", "话没说完", "让你猜"]', 0.8, 'public'),
        ('language_habit', '习惯用敬语',   '["您", "请问", "麻烦您", "不好意思", "客气"]', 0.7, 'public'),
        ('language_habit', '说话带刺',     '["阴阳怪气", "反讽", "话里有话", "不正面回答", "冷嘲热讽"]', 0.7, 'public'),

        -- ---- typing_habit（打字习惯）15条 ----
        ('typing_habit', '爱用表情包',       '["每条消息配图", "用表情代替文字", "收藏大量表情", "斗图", "表情包比话多"]', 1.3, 'public'),
        ('typing_habit', '喜欢发语音转文字', '["懒得打字", "语音识别错误多", "口语化", "语速快", "不想看屏幕"]', 1.0, 'public'),
        ('typing_habit', '从不用标点',       '["一逗到底", "空格代替标点", "看的人累", "随性", "懒得按符号键"]', 1.1, 'public'),
        ('typing_habit', '爱用感叹号',       '["每句结尾感叹", "情绪强烈", "热情", "急迫感", "像在喊"]', 1.0, 'public'),
        ('typing_habit', '喜欢分段发送',     '["一句一段", "消息碎片化", "连续发送", "不等回复", "刷屏"]', 1.1, 'public'),
        ('typing_habit', '一句到底不分段',   '["长消息", "不换行", "一大坨文字", "看着累", "信息密度高"]', 0.9, 'public'),
        ('typing_habit', '爱用波浪线',       '["~", "语气轻柔", "卖萌", "撒娇", "软绵绵"]', 0.8, 'public'),
        ('typing_habit', '喜欢用句号结尾',   '["每句都加句号", "正式", "严谨", "像写文章", "有始有终"]', 0.7, 'public'),
        ('typing_habit', '爱发长消息',       '["小作文", "详细描述", "逻辑完整", "有开头结尾", "信息量大"]', 0.8, 'public'),
        ('typing_habit', '喜欢用数字编号',   '["1. 2. 3.", "条理清晰", "列要点", "强迫症", "逻辑性强"]', 0.7, 'public'),
        ('typing_habit', '爱用问号',         '["???连续问号", "质疑", "惊讶", "不确定", "追问"]', 0.9, 'public'),
        ('typing_habit', '习惯打空格',       '["中英文之间加空格", "排版强迫症", "美观", "间隔清晰", "程序员风格"]', 0.6, 'public'),
        ('typing_habit', '爱用省略号',       '["……", "话没说完", "意味深长", "犹豫", "留悬念"]', 0.8, 'public'),
        ('typing_habit', '喜欢用英文标点',   '[",", ".", "?", "半角标点", "英文输入法不切换"]', 0.7, 'public'),
        ('typing_habit', '发消息前喜欢撤回修改', '["反复编辑", "追求完美", "措辞谨慎", "撤回重发", "犹豫"]', 0.6, 'public'),

        -- ---- scene（场景）12条 ----
        ('scene', '赶时间',   '["语速快", "短句", "不寒暄", "催促", "走路都在打字"]', 1.2, 'public'),
        ('scene', '心情不好', '["不想说话", "回复慢", "语气冷淡", "容易发火", "沉默"]', 1.1, 'public'),
        ('scene', '刚起床',   '["迷糊", "反应慢", "简短回复", "还没清醒", "赖床中"]', 0.9, 'public'),
        ('scene', '睡前',     '["困倦", "话少", "感性", "容易走心", "胡思乱想"]', 0.9, 'public'),
        ('scene', '通勤中',   '["地铁上", "信号不好", "单手打字", "看消息不及时", "挤"]', 1.1, 'public'),
        ('scene', '吃饭时',   '["边吃边看手机", "回复慢", "可能发美食图", "嘴里有东西", "随意"]', 0.8, 'public'),
        ('scene', '运动后',   '["出汗", "喘", "兴奋", "想分享", "精力旺盛"]', 0.6, 'public'),
        ('scene', '加班中',   '["疲惫", "烦躁", "想下班", "摸鱼聊天", "注意力分散"]', 1.0, 'public'),
        ('scene', '逛街时',   '["看东西", "拍照分享", "回复断断续续", "兴奋", "消费冲动"]', 0.7, 'public'),
        ('scene', '带娃中',   '["注意力被分散", "回复慢", "话题围绕孩子", "手忙脚乱", "随时被打断"]', 0.9, 'public'),
        ('scene', '看病时',   '["焦虑", "等叫号", "关注症状", "想快点结束", "不安"]', 0.7, 'public'),
        ('scene', '聚会中',   '["社交模式", "话多", "偶尔看手机", "热闹", "分享现场"]', 0.7, 'public'),

        -- ---- education（教育程度）10条 ----
        ('education', '初中',     '["用词简单", "口语化", "少书面语", "方言多", "表达直接"]', 1.0, 'public'),
        ('education', '高中',     '["基础表达", "偶尔用成语", "常识面广", "对某些领域有了解", "表达尚可"]', 1.0, 'public'),
        ('education', '大专',     '["专业方向明确", "实用导向", "表达清楚", "动手能力强", "理论少"]', 1.0, 'public'),
        ('education', '本科',     '["表达完整", "逻辑清晰", "知识面广", "会查资料", "书面语能力好"]', 1.1, 'public'),
        ('education', '硕士',     '["学术思维", "严谨", "数据驱动", "专业深度", "批判性思维"]', 0.8, 'public'),
        ('education', '博士',     '["深度专业", "引用文献", "措辞严谨", "怀疑精神", "学术腔"]', 0.5, 'public'),
        ('education', '中专',     '["技能导向", "实用主义", "表达朴素", "动手能力强", "理论少"]', 0.8, 'public'),
        ('education', '职高',     '["职业化", "实操强", "表达简单", "早入社会", "务实"]', 0.7, 'public'),
        ('education', '小学',     '["表达简单", "词汇量少", "拼音多", "错别字", "天真"]', 0.5, 'public'),
        ('education', '成人自考', '["上进", "边工边学", "时间紧", "目标明确", "自律"]', 0.7, 'public');

        RAISE NOTICE '已插入 persona_traits 种子数据（101条）';
    ELSE
        RAISE NOTICE 'persona_traits 已有数据，跳过种子插入';
    END IF;
END
$$;

-- ============================================================
-- 3.2 元提示模板种子数据（meta_prompt_templates）
-- 6 套模板，覆盖不同生成风格
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM meta_prompt_templates LIMIT 1) THEN
        INSERT INTO meta_prompt_templates (template, scope, enabled, weight) VALUES
        (
            '你是一个{{role}}，当前心情{{mood}}，场景是{{scene}}。你的语言习惯是{{quirk}}。请用这个身份提出一个关于{{domain}}的问题，要求自然、口语化，不要像AI生成的内容。',
            'public', TRUE, 1.0
        ),
        (
            '假设你是一位{{role}}，现在{{scene}}，心情有点{{mood}}。你说话风格{{quirk}}。请针对「{{domain}}」写一条你平时会发的消息，就像你在微信群里随口说的一样。',
            'public', TRUE, 1.2
        ),
        (
            E'角色：{{role}}\n当前状态：{{scene}}，{{mood}}\n语言风格：{{quirk}}\n画像详情：\n{{descriptions}}\n任务：针对「{{domain}}」生成一条自然的人类提问\n注意：避免使用过于正式或书面化的表达，模拟真实用户输入。',
            'public', TRUE, 0.8
        ),
        (
            '你正在{{scene}}，作为一个{{role}}，你此刻感到{{mood}}。你的说话方式{{quirk}}。现在你需要搜索或询问关于「{{domain}}」的信息，请直接写出你会输入的内容，不需要解释。',
            'public', TRUE, 1.1
        ),
        (
            E'请模拟以下用户画像发出的一条消息：\n- 身份：{{role}}\n- 当前场景：{{scene}}\n- 情绪状态：{{mood}}\n- 语言习惯：{{quirk}}\n画像详情：\n{{descriptions}}\n话题：「{{domain}}」\n要求：像真人一样随意、自然，可以有错别字或口语化表达。',
            'public', TRUE, 0.9
        ),
        (
            '以{{role}}的身份，在{{scene}}的情况下，带着{{mood}}的情绪，用{{quirk}}的语气，表达对「{{domain}}」的看法或提问。直接输出内容，不要加引号或前缀。',
            'public', TRUE, 1.0
        );

        RAISE NOTICE '已插入 meta_prompt_templates 种子数据（6条）';
    ELSE
        RAISE NOTICE 'meta_prompt_templates 已有数据，跳过种子插入';
    END IF;
END
$$;

-- ============================================================
-- 3.3 后处理规则种子数据（postprocess_rules）
-- 7 条规则，模拟人类打字习惯
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM postprocess_rules LIMIT 1) THEN
        INSERT INTO postprocess_rules (name, description, probability, params, scope, enabled, sort_order) VALUES
        (
            'prefix_filler',
            '在开头插入口语化填充词',
            0.1,
            '{"fillers": ["对了，", "突然想起来，", "话说，", "诶，"]}'::jsonb,
            'public', TRUE, 1
        ),
        (
            'replace_de',
            '将"的"替换为"滴"',
            0.2,
            '{"probability": 0.3}'::jsonb,
            'public', TRUE, 2
        ),
        (
            'randomize_punctuation',
            '随机替换或删除标点符号',
            0.15,
            '{}'::jsonb,
            'public', TRUE, 3
        ),
        (
            'insert_filler_words',
            '在句中插入无意义语气词',
            0.2,
            '{"filler_words": ["唔", "额", "那个"], "max_insertions": 2}'::jsonb,
            'public', TRUE, 4
        ),
        (
            'lowercase_start',
            '将句首大写字母改为小写',
            0.1,
            '{"probability": 0.5}'::jsonb,
            'public', TRUE, 5
        ),
        (
            'mess_spacing',
            '随机在中英文之间添加或删除空格',
            0.1,
            '{"add_space_probability": 0.3, "remove_space_probability": 0.5}'::jsonb,
            'public', TRUE, 6
        ),
        (
            'remove_punctuation',
            '随机删除某些标点符号',
            0.15,
            '{"probability": 0.2, "punctuation_marks": ["。", "，", "！", "？", "；", "："]}'::jsonb,
            'public', TRUE, 7
        );

        RAISE NOTICE '已插入 postprocess_rules 种子数据（7条）';
    ELSE
        RAISE NOTICE 'postprocess_rules 已有数据，跳过种子插入';
    END IF;
END
$$;

-- ============================================================
-- 3.4 模型配置种子数据（model_configs）
-- 18 个模型配置，覆盖 4 种 Provider 类型
-- api_key_encrypted 全部为 NULL，需通过前端管理页面填写 API Key
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM model_configs LIMIT 1) THEN
        INSERT INTO model_configs (name, provider_type, api_key_encrypted, base_url, model_name, weight, max_tokens, timeout, scope, enabled) VALUES
        -- ---- OpenAI 兼容接口 ----
        ('deepseek-chat',   'openai',    NULL, 'https://api.deepseek.com/v1',                             'deepseek-chat',                  1.0, 256, 30, 'public', TRUE),
        ('gemini-2.0-flash','openai',    NULL, 'https://generativelanguage.googleapis.com/v1beta/openai',  'gemini-2.0-flash',               1.0, 256, 30, 'public', FALSE),
        ('mistral-large',   'openai',    NULL, 'https://api.mistral.ai/v1',                               'mistral-large-latest',           0.8, 256, 30, 'public', FALSE),
        ('llama-3-70b',     'openai',    NULL, 'https://api.siliconflow.cn/v1',                           'meta-llama/Meta-Llama-3.1-70B-Instruct', 0.7, 256, 30, 'public', FALSE),
        ('kimi-moonshot',   'openai',    NULL, 'https://api.moonshot.cn/v1',                              'moonshot-v1-8k',                 0.9, 256, 30, 'public', FALSE),
        ('qwen-plus',       'openai',    NULL, 'https://dashscope.aliyuncs.com/compatible-mode/v1',       'qwen-plus',                      1.0, 256, 30, 'public', FALSE),
        ('siliconflow-qwen','openai',    NULL, 'https://api.siliconflow.cn/v1',                           'Qwen/Qwen2.5-72B-Instruct',     0.8, 256, 30, 'public', FALSE),
        ('doubao-pro',      'openai',    NULL, 'https://ark.cn-beijing.volces.com/api/v3',                'doubao-pro-32k',                 0.9, 256, 30, 'public', FALSE),
        ('ernie-4.0',       'openai',    NULL, 'https://qianfan.baidubce.com/v2',                         'ernie-4.0-8k',                   0.9, 256, 30, 'public', FALSE),
        ('hunyuan-lite',    'openai',    NULL, 'https://api.hunyuan.cloud.tencent.com/v1',                'hunyuan-lite',                   0.8, 256, 30, 'public', FALSE),
        ('minimax-abab',    'openai',    NULL, 'https://api.minimax.chat/v1',                             'abab6.5s-chat',                  0.8, 256, 30, 'public', FALSE),
        ('step-2-16k',      'openai',    NULL, 'https://api.stepfun.com/v1',                              'step-2-16k',                     0.8, 256, 30, 'public', FALSE),
        ('yi-large',        'openai',    NULL, 'https://api.lingyiwanwu.com/v1',                          'yi-large',                       0.8, 256, 30, 'public', FALSE),
        ('glm-4-flash',     'openai',    NULL, 'https://open.bigmodel.cn/api/paas/v4',                    'glm-4-flash',                    0.8, 256, 30, 'public', FALSE),
        ('gpt-4o-mini',     'openai',    NULL, 'https://api.openai.com/v1',                               'gpt-4o-mini',                    1.0, 256, 30, 'public', FALSE),
        -- ---- Anthropic 原生接口 ----
        ('claude-3-5-sonnet','anthropic', NULL, 'https://api.anthropic.com',                              'claude-3-5-sonnet-20241022',     1.0, 256, 30, 'public', FALSE),
        -- ---- Azure OpenAI ----
        ('azure-gpt-4o-mini','azure',    NULL, 'https://YOUR_RESOURCE.openai.azure.com',                  'gpt-4o-mini',                    1.0, 256, 30, 'public', FALSE),
        -- ---- Amazon Bedrock ----
        ('bedrock-claude',  'bedrock',   NULL, 'https://bedrock-runtime.us-east-1.amazonaws.com',         'anthropic.claude-3-5-sonnet-20241022-v2:0', 0.9, 256, 30, 'public', FALSE);

        RAISE NOTICE '已插入 model_configs 种子数据（18条）';
    ELSE
        RAISE NOTICE 'model_configs 已有数据，跳过种子插入';
    END IF;
END
$$;

-- ============================================================
-- 数据初始化完成
-- ============================================================
