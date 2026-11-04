package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import java.io.Serializable;

/** 每场景每站的常量与阈值（复合主键） */
@Entity
@Table(name = "scenario_site_param")
@IdClass(ScenarioSiteParam.Key.class)
public class ScenarioSiteParam {
    @Id
    public String scenarioId;
    @Id
    public String siteId;
    public int capacityPerBucket;
    public int kappaQ;
    public int kappaI;
    public int i0;
    public int counters;

    public static class Key implements Serializable {
        public String scenarioId;
        public String siteId;
    }
}