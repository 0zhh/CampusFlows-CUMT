package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;

/** 室内一排货架 */
@Entity
@Table(name = "rack_row")
public class RackRow {
    @Id
    public String id;
    public String siteId;
    public String zoneId;
    public int colNo;
    public int rowNo;
    @jakarta.persistence.Column(name = "x_m")
    public BigDecimal xM;
    @jakarta.persistence.Column(name = "y_m")
    public BigDecimal yM;
    @jakarta.persistence.Column(name = "length_m")
    public BigDecimal lengthM;
    @jakarta.persistence.Column(name = "depth_m")
    public BigDecimal depthM;
    public String managedBy;
}