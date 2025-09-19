from datetime import datetime, timezone
from app.db import db


class MenuInRole(db.Model):
    __tablename__ = 'menu_in_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    # can_read = db.Column(db.Boolean, default=True, nullable=False)
    # can_write = db.Column(db.Boolean, default=False, nullable=False)
    # can_delete = db.Column(db.Boolean, default=False, nullable=False)
    created_on = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    # assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    role = db.relationship('Role', back_populates='role_menus')
    menu = db.relationship('MenuItem', back_populates='menu_roles')
    
    # assigner = db.relationship('User')
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('role_id', 'menu_id', name='unique_role_menu'),)
    
    def __repr__(self):
        return f'<MenuInRole role_id={self.role_id} menu_id={self.menu_id}>'
 
    
    