package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** 单个货架 */
@Entity
@Table(name = "shelf")
public class Shelf {
    @Id
    public String id;
    public String rowId;
    public int bayNo;
    public short tiers;
    public short slotsPerTier;
}