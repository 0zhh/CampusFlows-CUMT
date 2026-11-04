package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** 演示场景 */
@Entity
@Table(name = "scenario")
public class Scenario {
    @Id
    public String id;
    public String name;
    public Integer dayIndex;
    public String note;
}