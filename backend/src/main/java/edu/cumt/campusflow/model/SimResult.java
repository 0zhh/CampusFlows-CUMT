package edu.cumt.campusflow.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import java.io.Serializable;

/** 某次运行下逐桶结果 */
@Entity
@Table(name = "sim_result")
@IdClass(SimResult.Key.class)
public class SimResult {
    @Id
    public Long runId;
    @Id
    public String siteId;
    @Id
    @Column(columnDefinition = "CHAR(5)")
    public String bucket;
    public int q;
    public int i;
    public int s;
    public int p;
    public int unmet;
    @jakarta.persistence.Column(name = "risk_q")
    public boolean riskQ;
    @jakarta.persistence.Column(name = "risk_i")
    public boolean riskI;

    public static class Key implements Serializable {
        public Long runId;
        public String siteId;
        public String bucket;
    }
}