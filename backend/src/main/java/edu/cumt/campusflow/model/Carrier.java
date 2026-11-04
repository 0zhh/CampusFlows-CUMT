package edu.cumt.campusflow.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** 承运商字典 */
@Entity
@Table(name = "carrier")
public class Carrier {
    @Id
    public String code;
    public String name;
}