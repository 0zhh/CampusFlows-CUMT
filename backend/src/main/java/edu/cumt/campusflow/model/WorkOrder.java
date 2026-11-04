package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

/** 风险工单：由仿真越限时段派生，可在页面上流转 */
@Entity
@Table(name = "work_order")
public class WorkOrder {
    @Id
    private String id;
    private String siteId;
    private String kind;
    private String status;
    @jakarta.persistence.Column(columnDefinition = "CHAR(5)")
    private String bucket;
    private String title;
    private String detail;
    private Instant updatedAt;

    protected WorkOrder() {
    }

    public WorkOrder(String id, String siteId, String kind, String status,
                     String bucket, String title, String detail) {
        this.id = id; this.siteId = siteId; this.kind = kind; this.status = status;
        this.bucket = bucket; this.title = title; this.detail = detail;
        this.updatedAt = Instant.now();
    }

    public String getId() { return id; }
    public String getSiteId() { return siteId; }
    public String getKind() { return kind; }
    public String getStatus() { return status; }
    public String getBucket() { return bucket; }
    public String getTitle() { return title; }
    public String getDetail() { return detail; }
    public Instant getUpdatedAt() { return updatedAt; }

    public void setStatus(String status) { this.status = status; this.updatedAt = Instant.now(); }
}
