package edu.cumt.campusflow.service;

import edu.cumt.campusflow.model.Site;
import edu.cumt.campusflow.model.WorkOrder;
import edu.cumt.campusflow.repo.SiteRepository;
import edu.cumt.campusflow.repo.WorkOrderRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

/** 首次启动时把站点与演示工单写进 H2；MySQL 形态下数据已由 SQL 灌好，不再写库 */
@Component
@Profile("dev")
public class SeedService implements CommandLineRunner {

    private final SiteRepository sites;
    private final WorkOrderRepository orders;

    public SeedService(SiteRepository sites, WorkOrderRepository orders) {
        this.sites = sites;
        this.orders = orders;
    }

    @Override
    public void run(String... args) {
        if (sites.count() == 0) {
            sites.save(new Site("NH-TAOYUAN", "桃苑物流服务中心", "main_hub",
                    "08:30", "18:30", 19200, 16320, 14320, 298, 0.8, 2, "observed"));
            sites.save(new Site("NH-SONGYUAN", "松苑无人菜鸟驿站", "unmanned",
                    "07:00", "23:30", 2500, 2125, 480, 197, 0.8, 1, "assumed"));
            sites.save(new Site("NH-MEIYUAN", "梅苑无人菜鸟驿站", "unmanned",
                    "07:00", "23:30", 2230, 1895, 430, 167, 0.8, 1, "assumed"));
            sites.save(new Site("NH-LANYUAN", "兰苑无人菜鸟驿站", "unmanned",
                    "07:00", "23:30", 1770, 1505, 350, 137, 0.8, 1, "assumed"));
        }
        if (orders.count() == 0) {
            orders.save(new WorkOrder("WO-001", "NH-SONGYUAN", "exceed", "open",
                    "14:30", "松苑 待取区超限", "在架件数越过运营上限，需引导取件或扩临时周转区"));
            orders.save(new WorkOrder("WO-002", "NH-MEIYUAN", "exceed", "doing",
                    "15:00", "梅苑 待取区超限", "已开放临时待取区，持续跟进"));
            orders.save(new WorkOrder("WO-003", "NH-LANYUAN", "watch", "closed",
                    "16:00", "兰苑 待取区接近上限", "高峰平稳度过，工单闭环"));
        }
    }
}
