package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** 站点静态档案 + 物理容量参数（容量来自实景照片与参数表） */
@Entity
@Table(name = "site")
public class Site {
    @Id
    private String id;
    private String name;
    private String role;
    private String openTime;
    private String closeTime;
    private int physicalSlots;
    private int kappaI;
    private int kappaQ;
    private int capacityPerBucket;
    private double aisleM;
    private int counters;
    private String physicalSource;

    protected Site() {
    }

    public Site(String id, String name, String role, String openTime, String closeTime,
                int physicalSlots, int kappaI, int kappaQ, int capacityPerBucket,
                double aisleM, int counters, String physicalSource) {
        this.id = id; this.name = name; this.role = role;
        this.openTime = openTime; this.closeTime = closeTime;
        this.physicalSlots = physicalSlots; this.kappaI = kappaI; this.kappaQ = kappaQ;
        this.capacityPerBucket = capacityPerBucket; this.aisleM = aisleM;
        this.counters = counters; this.physicalSource = physicalSource;
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getRole() { return role; }
    public String getOpenTime() { return openTime; }
    public String getCloseTime() { return closeTime; }
    public int getPhysicalSlots() { return physicalSlots; }
    public int getKappaI() { return kappaI; }
    public int getKappaQ() { return kappaQ; }
    public int getCapacityPerBucket() { return capacityPerBucket; }
    public double getAisleM() { return aisleM; }
    public int getCounters() { return counters; }
    public String getPhysicalSource() { return physicalSource; }

    public void setCounters(int counters) { this.counters = counters; }
}
