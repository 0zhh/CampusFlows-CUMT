-- ============================================================
--  CampusFlow / 驿链 · MySQL 8.4 建表脚本 V1
--  15 张表；InnoDB / utf8mb4_0900_ai_ci
--  幂等：重复执行不报错（CREATE TABLE IF NOT EXISTS）
-- ============================================================
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ---------- 1. 站点 ----------
CREATE TABLE IF NOT EXISTS site (
  id                   VARCHAR(32)  NOT NULL COMMENT '站点编号',
  name                 VARCHAR(64)  NOT NULL COMMENT '站点名称',
  role                 VARCHAR(16)  NOT NULL COMMENT 'main_hub / unmanned',
  open_time            CHAR(5)      NOT NULL,
  close_time           CHAR(5)      NOT NULL,
  physical_slots       INT          NOT NULL COMMENT '物理储位（照片推算）',
  kappa_i              INT          NOT NULL COMMENT '待取运营上限 = 物理 × 85%',
  kappa_q              INT          NOT NULL COMMENT '积压上限',
  capacity_per_bucket  INT          NOT NULL COMMENT '每 30 分钟处理能力',
  aisle_m              DECIMAL(3,2) NOT NULL COMMENT '通道净宽',
  counters             TINYINT      NOT NULL COMMENT '自助机台数',
  physical_source      VARCHAR(16)  NOT NULL COMMENT 'observed / assumed',
  lat                  DECIMAL(9,6) NULL,
  lng                  DECIMAL(9,6) NULL,
  PRIMARY KEY (id),
  KEY idx_site_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='站点主档';

-- ---------- 2. 承运商 ----------
CREATE TABLE IF NOT EXISTS carrier (
  code VARCHAR(8)  NOT NULL,
  name VARCHAR(32) NOT NULL,
  PRIMARY KEY (code),
  UNIQUE KEY uk_carrier_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='承运商字典';

-- ---------- 3. 场景 ----------
CREATE TABLE IF NOT EXISTS scenario (
  id        VARCHAR(16)  NOT NULL,
  name      VARCHAR(64)  NOT NULL,
  day_index TINYINT      NOT NULL COMMENT '双十一第几天',
  note      VARCHAR(255) NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='演示场景';

-- ---------- 4. 场景 × 站点参数 ----------
CREATE TABLE IF NOT EXISTS scenario_site_param (
  scenario_id         VARCHAR(16) NOT NULL,
  site_id             VARCHAR(32) NOT NULL,
  capacity_per_bucket INT NOT NULL,
  kappa_q             INT NOT NULL,
  kappa_i             INT NOT NULL,
  i0                  INT NOT NULL,
  counters            TINYINT NOT NULL,
  PRIMARY KEY (scenario_id, site_id),
  CONSTRAINT fk_ssp_sc   FOREIGN KEY (scenario_id) REFERENCES scenario(id) ON DELETE CASCADE,
  CONSTRAINT fk_ssp_site FOREIGN KEY (site_id)     REFERENCES site(id)     ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='每场景每站的常量与阈值';

-- ---------- 5. 逐桶需求 ----------
CREATE TABLE IF NOT EXISTS demand_bucket (
  scenario_id VARCHAR(16) NOT NULL,
  site_id     VARCHAR(32) NOT NULL,
  bucket      CHAR(5)     NOT NULL,
  arrivals    INT NOT NULL,
  capacity    INT NOT NULL,
  pickups     INT NOT NULL,
  PRIMARY KEY (scenario_id, site_id, bucket),
  CONSTRAINT fk_db_sc   FOREIGN KEY (scenario_id) REFERENCES scenario(id) ON DELETE CASCADE,
  CONSTRAINT fk_db_site FOREIGN KEY (site_id)     REFERENCES site(id)     ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='逐 30 分钟到件/能力/取件';

-- ---------- 6. 参数版本 ----------
CREATE TABLE IF NOT EXISTS param_version (
  version      VARCHAR(16) NOT NULL,
  created_at   DATETIME(3) NOT NULL,
  observed_cnt SMALLINT NOT NULL,
  public_cnt   SMALLINT NOT NULL,
  assumed_cnt  SMALLINT NOT NULL,
  total_cnt    SMALLINT NOT NULL,
  payload      JSON NULL,
  PRIMARY KEY (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='参数版本快照';

-- ---------- 7. 仿真运行 ----------
CREATE TABLE IF NOT EXISTS simulation_run (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  scenario_id   VARCHAR(16)  NOT NULL,
  seed          INT          NOT NULL,
  param_version VARCHAR(16)  NULL,
  created_at    DATETIME(3)  NOT NULL,
  peak_i        INT          NOT NULL DEFAULT 0,
  risk_buckets  INT          NOT NULL DEFAULT 0,
  note          VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_run_created (created_at),
  CONSTRAINT fk_run_sc  FOREIGN KEY (scenario_id)   REFERENCES scenario(id)      ON DELETE CASCADE,
  CONSTRAINT fk_run_pv  FOREIGN KEY (param_version) REFERENCES param_version(version) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='一次仿真运行（历史）';

-- ---------- 8. 逐桶结果 ----------
CREATE TABLE IF NOT EXISTS sim_result (
  run_id   BIGINT      NOT NULL,
  site_id  VARCHAR(32) NOT NULL,
  bucket   CHAR(5)     NOT NULL,
  q        INT NOT NULL,
  i        INT NOT NULL,
  s        INT NOT NULL,
  p        INT NOT NULL,
  unmet    INT NOT NULL,
  risk_q   TINYINT(1) NOT NULL,
  risk_i   TINYINT(1) NOT NULL,
  PRIMARY KEY (run_id, site_id, bucket),
  CONSTRAINT fk_sr_run  FOREIGN KEY (run_id)  REFERENCES simulation_run(id) ON DELETE CASCADE,
  CONSTRAINT fk_sr_site FOREIGN KEY (site_id) REFERENCES site(id)           ON DELETE CASCADE,
  CONSTRAINT ck_sr_nonneg CHECK (q >= 0 AND i >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='逐桶 Q/I/S/P 结果';

-- ---------- 9. 工单 ----------
CREATE TABLE IF NOT EXISTS work_order (
  id         VARCHAR(16)  NOT NULL,
  site_id    VARCHAR(32)  NOT NULL,
  kind       VARCHAR(16)  NOT NULL COMMENT 'exceed / watch / drill',
  status     VARCHAR(16)  NOT NULL COMMENT 'open / doing / closed',
  bucket     CHAR(5)      NULL,
  title      VARCHAR(120) NOT NULL,
  detail     TEXT         NULL,
  created_at DATETIME(3)  NOT NULL,
  updated_at DATETIME(3)  NOT NULL,
  PRIMARY KEY (id),
  KEY idx_wo_site (site_id),
  KEY idx_wo_status (status),
  CONSTRAINT fk_wo_site FOREIGN KEY (site_id) REFERENCES site(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='风险工单';

-- ---------- 10. 工单事件 ----------
CREATE TABLE IF NOT EXISTS workorder_event (
  id          BIGINT      NOT NULL AUTO_INCREMENT,
  wo_id       VARCHAR(16) NOT NULL,
  from_status VARCHAR(16) NULL,
  to_status   VARCHAR(16) NOT NULL,
  actor       VARCHAR(32) NOT NULL,
  at_time     DATETIME(3) NOT NULL,
  note        VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_woe (wo_id, at_time),
  CONSTRAINT fk_woe FOREIGN KEY (wo_id) REFERENCES work_order(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工单状态流转流水';

-- ---------- 11. 货架排 ----------
CREATE TABLE IF NOT EXISTS rack_row (
  id         VARCHAR(16)  NOT NULL,
  site_id    VARCHAR(32)  NOT NULL,
  zone_id    VARCHAR(8)   NOT NULL COMMENT 'Z-C1 … Z-C6',
  col_no     TINYINT      NOT NULL,
  row_no     TINYINT      NOT NULL,
  x_m        DECIMAL(6,2) NOT NULL,
  y_m        DECIMAL(6,2) NOT NULL,
  length_m   DECIMAL(5,2) NOT NULL,
  depth_m    DECIMAL(4,2) NOT NULL,
  managed_by VARCHAR(8)   NOT NULL COMMENT 'SELF / JD',
  PRIMARY KEY (id),
  KEY idx_rr_site (site_id),
  CONSTRAINT fk_rr_site FOREIGN KEY (site_id) REFERENCES site(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='室内货架排';

-- ---------- 12. 货架 ----------
CREATE TABLE IF NOT EXISTS shelf (
  id              VARCHAR(24) NOT NULL,
  row_id          VARCHAR(16) NOT NULL,
  bay_no          SMALLINT    NOT NULL COMMENT '货架号',
  tiers           TINYINT     NOT NULL,
  slots_per_tier  SMALLINT    NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_shelf_bay (row_id, bay_no),
  KEY idx_shelf_bay (bay_no),
  CONSTRAINT fk_shelf_row FOREIGN KEY (row_id) REFERENCES rack_row(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='单个货架';

-- ---------- 13. 储位 ----------
CREATE TABLE IF NOT EXISTS slot (
  id        VARCHAR(32)  NOT NULL COMMENT 'S-191-3-12',
  shelf_id  VARCHAR(24)  NOT NULL,
  tier      TINYINT      NOT NULL,
  cell_no   SMALLINT     NOT NULL,
  parcel_id VARCHAR(32)  NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_slot_pos (shelf_id, tier, cell_no),
  UNIQUE KEY uk_slot_parcel (parcel_id),
  CONSTRAINT fk_slot_shelf FOREIGN KEY (shelf_id) REFERENCES shelf(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='储位';

-- ---------- 14. 包裹 ----------
CREATE TABLE IF NOT EXISTS parcel (
  id           VARCHAR(32) NOT NULL,
  site_id      VARCHAR(32) NOT NULL,
  carrier_code VARCHAR(8)  NOT NULL,
  size         CHAR(1)     NOT NULL,
  batch_id     VARCHAR(16) NULL,
  arrived_at   DATETIME    NULL,
  shelved_at   DATETIME    NULL,
  picked_at    DATETIME    NULL,
  status       VARCHAR(16) NOT NULL COMMENT 'in_transit / shelved / picked',
  PRIMARY KEY (id),
  KEY idx_parcel_site_status (site_id, status),
  KEY idx_parcel_carrier (carrier_code),
  CONSTRAINT fk_parcel_site    FOREIGN KEY (site_id)      REFERENCES site(id)    ON DELETE CASCADE,
  CONSTRAINT fk_parcel_carrier FOREIGN KEY (carrier_code) REFERENCES carrier(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='包裹（演示抽样）';

-- ---------- 15. 取件码 ----------
CREATE TABLE IF NOT EXISTS pickup_code (
  code      VARCHAR(16) NOT NULL COMMENT '108-3-2441',
  site_id   VARCHAR(32) NOT NULL,
  parcel_id VARCHAR(32) NOT NULL,
  issued_at DATETIME    NOT NULL,
  PRIMARY KEY (site_id, code),
  UNIQUE KEY uk_pc_parcel (parcel_id),
  KEY idx_pc_code (code),
  CONSTRAINT fk_pc_site   FOREIGN KEY (site_id)   REFERENCES site(id)   ON DELETE CASCADE,
  CONSTRAINT fk_pc_parcel FOREIGN KEY (parcel_id) REFERENCES parcel(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='取件码';

SET FOREIGN_KEY_CHECKS = 1;
