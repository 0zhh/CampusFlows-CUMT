package edu.cumt.campusflow.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import java.io.Serializable;

/** 逐 30 分钟到件/处理能力/取件需求 */
@Entity
@Table(name = "demand_bucket")
@IdClass(DemandBucket.Key.class)
public class DemandBucket {
    @Id
    public String scenarioId;
    @Id
    public String siteId;
    @Id
    @Column(columnDefinition = "CHAR(5)")
    public String bucket;
    public int arrivals;
    public int capacity;
    public int pickups;

    public static class Key implements Serializable {
        public String scenarioId;
        public String siteId;
        public String bucket;
    }
}