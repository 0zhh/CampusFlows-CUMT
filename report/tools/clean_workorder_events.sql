USE campusflow;
DELETE FROM workorder_event;
UPDATE work_order SET status = CASE id
  WHEN 'WO-001' THEN 'closed'
  WHEN 'WO-002' THEN 'doing'
  WHEN 'WO-003' THEN 'closed'
  WHEN 'WO-004' THEN 'closed' END;

INSERT INTO workorder_event (wo_id, from_status, to_status, actor, at_time, note) VALUES
('WO-001', NULL,      'open',   '系统',     '2026-11-04 08:10:00.000', '仿真监测到待取库存接近上限，自动建单'),
('WO-001', 'open',    'doing',  '站点值守', '2026-11-04 09:30:00.000', '开放临时待取区，在取件高峰前推送提醒短信'),
('WO-001', 'doing',   'closed', '调度员',   '2026-11-04 11:00:00.000', '占用回落至 78%，工单闭环'),
('WO-002', NULL,      'open',   '系统',     '2026-11-04 11:30:00.000', '仿真监测到待取库存 6722 件超过上限 6715 件，自动建单'),
('WO-002', 'open',    'doing',  '调度员',   '2026-11-04 11:45:00.000', '增派 1 名值守人员，并申请跨站调拨'),
('WO-003', NULL,      'open',   '系统',     '2026-11-04 13:10:00.000', '仿真监测到待取库存超过上限，自动建单'),
('WO-003', 'open',    'closed', '站点值守', '2026-11-04 14:05:00.000', '引导自助取件，占用回落，闭环'),
('WO-004', NULL,      'open',   '系统',     '2026-11-04 15:00:00.000', '仿真监测到待取区占用达 92%，自动建单'),
('WO-004', 'open',    'doing',  '调度员',   '2026-11-04 15:20:00.000', '开放备用货架，转移大件至临时区'),
('WO-004', 'doing',   'closed', '站点值守', '2026-11-04 17:40:00.000', '晚高峰前回落，工单闭环');
