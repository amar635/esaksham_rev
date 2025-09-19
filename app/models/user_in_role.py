from datetime import datetime, timezone
from app.db import db


class UserInRole(db.Model):
    __tablename__ = 'users_in_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    created_on = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    # assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='user_roles')
    role = db.relationship('Role', back_populates='role_users')
    # assigner = db.relationship('User', foreign_keys=[assigned_by])
    
    # Composite unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),)
    
    def __repr__(self):
        return f'<UserInRole user_id={self.user_id} role_id={self.role_id}>'
