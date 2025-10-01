from collections import defaultdict
from datetime import datetime
from sqlalchemy import case, desc, func
from app.db import db
import logging

from app.models import State_UT, District, Block, User
from app.models.courses import Course

# Centralized activity and error loggers
# try:
#     from app import activity_logger, error_logger
# except ImportError:
#     activity_logger = logging.getLogger('activity')
#     error_logger = logging.getLogger('error')

class UserCourse(db.Model):
    __tablename__ = 'user_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    certificate_issued = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __init__(self, user_id, course_id, certificate_issued, timestamp=None):
        try:
            if timestamp is None:
                timestamp = datetime.now()
            self.user_id = user_id
            self.course_id = course_id
            self.timestamp = timestamp
            self.certificate_issued = certificate_issued
            # activity_logger.info(f"User completed course: {self.course_id}, user_id={self.user_id}")
        except Exception as ex:
            # error_logger.error(f"Error saving status for User {user_id}: {ex}")
            pass

    def json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'certificate_issued': self.certificate_issued,
            'timestamp': self.timestamp
        }
        
        
    @classmethod
    def find_by_user_and_course_id(cls, user_id, course_id):
        try:
            return cls.query.filter_by(user_id=user_id, course_id=course_id).first()
        except Exception as ex:
            # error_logger.error(f"Error finding CourseStatus for user_id={user_id}, course={course_id}: {ex}")
            return None
        
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            # activity_logger.info(f"Saved CourseStatus for user_id={self.user_id}, course={self.course_id}")
        except Exception as ex:
            db.session.rollback()
            # error_logger.error(f"Error saving CourseStatus for user_id={self.user_id}, course={self.course_id}: {ex}")
            raise ex
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            # activity_logger.info(f"Deleted CourseStatus for user_id={self.user_id}, course={self.course_id}")
        except Exception as ex:
            db.session.rollback()
            # error_logger.error(f"Error deleting CourseStatus for user_id={self.user_id}, course={self.course_id}: {ex}")
            raise ex
    
    def commit_db(self):
        try:
            db.session.commit()
            # activity_logger.info(f"Committed CourseStatus for user_id={self.user_id}, course={self.course_id}")
        except Exception as ex:
            db.session.rollback()
            # error_logger.error(f"Error committing CourseStatus for user_id={self.user_id}, course={self.course_id}: {ex}")
            raise ex
    
    def update_db(self, data):
        try:
            for key, value in data.items():
                setattr(self, key, value)
            self.commit_db()
            # activity_logger.info(f"Updated CourseStatus for user_id={self.user_id}, course={self.course_id}")
        except Exception as ex:
            # error_logger.error(f"Error updating CourseStatus for user_id={self.user_id}, course={self.course_id}: {ex}")
            raise ex
        
    @classmethod
    def get_certified_users(cls,state_id=None,district_id=None,block_id=None):
        try:
            query = db.session.query(
                func.count(cls.id)
            ).join(
                User, User.id == cls.user_id
            ).filter(cls.certificate_issued == True)
            
            if state_id:
                query = query.filter(User.state_id == state_id)
            if district_id:
                query = query.filter(User.district_id == district_id)
            if block_id:
                query = query.filter(User.block_id == block_id)
                
            return query.scalar() or 0
        except Exception as ex:
            # error_logger.error(f"Error getting certified users: {ex}")
            return 0
        """
        SELECT count(uc.id) FROM public.user_courses AS uc
        inner join "user" u on u.id = uc.user_id 
        where u.state_id = 10
        """

    @classmethod
    def get_state_wise_users(cls, top_5=None):
        try:
            q = (
                db.session.query(
                    State_UT.id.label("id"),
                    State_UT.name.label("name"),
                    State_UT.short_name.label("short_name"),
                    func.count(cls.id).label("value")
                )
                .join(User, User.id == cls.user_id)
                .join(State_UT, State_UT.id == User.state_id)
                .group_by(State_UT.id, State_UT.name, State_UT.short_name)
                .order_by(desc(func.count(cls.id)))
            )
            if top_5:
                q = q.limit(5)

            rows = q.all()
            return [dict(r._mapping) for r in rows]
        except Exception as ex:
            # error_logger.error(f"Error getting state-wise users: {ex}")
            return []
        """
        SELECT s.name as name,s.id as id ,count(uc.id) as value FROM public.user_courses AS uc
        inner join "user" u on u.id = uc.user_id 
        inner join states s on s.id = u.state_id 
        group by s.name,s.id
        order by count(uc.id) desc
        limit 5
        """

    @classmethod
    def get_all_district_wise_users(cls, state_ids, top_5=False):
        try:
            if not state_ids:
                return []

            q = (
                db.session.query(
                    District.id.label("id"),
                    District.name.label("name"),
                    District.short_name.label("short_name"),
                    User.state_id.label("state_id"),
                    func.count(cls.id).label("value")
                )
                .join(User, User.id == cls.user_id)
                .join(District, District.id == User.district_id)
                .filter(User.state_id.in_(state_ids))
                .group_by(District.id, District.name, District.short_name, User.state_id)
            )

            rows = [dict(r._mapping) for r in q.all()]

            # group by stateId
            grouped = defaultdict(list)
            for r in rows:
                grouped[r["state_id"]].append(r)

            out = []
            for sid, items in grouped.items():
                # ✅ always sort
                items.sort(key=lambda x: (-x["value"], x["name"]))
                if top_5:
                    out.extend(items[:5])
                else:
                    out.extend(items)

            return out

        except Exception as ex:
            # error_logger.error(f"Error getting batch district-wise users: {ex}")
            return []


    # --- BLOCKS (batch; top-5 PER DISTRICT in Python) ---
    @classmethod
    def get_all_block_wise_users(cls, district_ids, top_5=False):
        try:
            if not district_ids:
                return []

            q = (
                db.session.query(
                    Block.id.label("id"),
                    Block.name.label("name"),
                    Block.short_name.label("short_name"),
                    User.district_id.label("district_id"),
                    func.count(cls.id).label("value")
                )
                .join(User, User.id == cls.user_id)
                .join(Block, Block.id == User.block_id)
                .filter(User.district_id.in_(district_ids))
                .group_by(Block.id, Block.name, Block.short_name, User.district_id)
            )

            rows = [dict(r._mapping) for r in q.all()]

            grouped = defaultdict(list)
            for r in rows:
                grouped[r["district_id"]].append(r)

            out = []
            for did, items in grouped.items():
                items.sort(key=lambda x: (-x["value"], x["name"]))
                if top_5:
                    out.extend(items[:5])
                else:
                    out.extend(items)

            return out

        except Exception as ex:
            # error_logger.error(f"Error getting batch block-wise users: {ex}")
            return []


    # --- USERS (batch; include blockId + course for frontend compatibility) ---
    @classmethod
    def get_all_users_in_blocks(cls, block_ids):
        try:
            if not block_ids:
                return []

            q = (
                db.session.query(
                    User.id.label("id"),
                    User.name.label("name"),
                    User.email.label("email"),
                    User.block_id.label("block_id"),
                    func.to_char(cls.timestamp, 'YYYY-MM-DD HH24:MI:SS').label("timestamp"),
                    Course.name.label("course")
                )
                .join(User, User.id == cls.user_id)
                .join(Course, cls.course_id == Course.id)
                .filter(User.block_id.in_(block_ids))
            )

            rows = [dict(r._mapping) for r in q.all()]

            # ✅ sort users: newest timestamp first, then name
            rows.sort(key=lambda x: (x["name"] or "").lower())

            return rows

        except Exception as ex:
            # error_logger.error(f"Error getting batch users in blocks: {ex}")
            return []
        
    @classmethod
    def get_state_count(cls):
        try:
            query = (
                db.session.query(
                    func.coalesce(State_UT.name, "Untracked").label("state_name"),
                    State_UT.short_name,
                    State_UT.id,
                    State_UT.uuid,
                    func.count(User.id).label("state_count"),
                )
                .select_from(UserCourse)
                .outerjoin(User, User.id == UserCourse.user_id)
                .outerjoin(State_UT, State_UT.id == User.state_id)
                .group_by(State_UT.id)
                .order_by(
                    case(
                        (func.coalesce(State_UT.name, "Untracked") == "Untracked", 1),
                        else_=0,
                    ),
                    func.count(User.id).desc(),
                )
            )
            states_data = query.all()
            results = []
            for state in states_data:
                results.append({
                    'id': state.id,
                    'name': state.state_name,
                    'user_count': state.state_count
                })
            return results
        except Exception as ex:
            # error_logger.error(f"Error retriving user_course : {ex}")
            raise ex
    
    @classmethod
    def get_district_count(cls, state_id):
        try:
            query = (
                db.session.query(
                    func.coalesce(District.name, "Untracked").label("district_name"),
                    District.short_name,
                    District.id,
                    func.count(User.id).label("district_count"),
                )
                .select_from(UserCourse)
                .outerjoin(User, User.id == UserCourse.user_id)
                .outerjoin(District, District.id == User.district_id)
                # .join(District, State_UT.id == District.state_id)
                .filter(District.state_id == state_id)\
                # .outerjoin(Block, District.id == Block.district_id)
                # .join(User, Block.id == User.block_id)
                .group_by(District.id,District.name)
                .order_by(
                    case(
                        (func.coalesce(District.name, "Untracked") == "Untracked", 1),
                        else_=0,
                    ),
                    func.count(User.id).desc(),
                )
            )
            districts_data = query.all()
            results = []
            for district in districts_data:
                results.append({
                    'id': district.id,
                    'name': district.district_name,
                    'user_count': district.district_count,
                    'state_id': state_id
                })
            return results
        except Exception as ex:
            # error_logger.error(f"Error retriving user_course : {ex}")
            raise ex

    @classmethod
    def get_block_count(cls, state_id, district_id):
        try:
            query = (
                db.session.query(
                    func.coalesce(Block.name, "Untracked").label("block_name"),
                    Block.short_name,
                    Block.id,
                    func.count(User.id).label("block_count"),
                )
                .select_from(UserCourse)
                .outerjoin(User, User.id == UserCourse.user_id)
                .outerjoin(Block, Block.id == User.block_id)
                .filter(Block.district_id == district_id, Block.state_id == state_id)
                .group_by(Block.id,Block.name)
                .order_by(
                    case(
                        (func.coalesce(Block.name, "Untracked") == "Untracked", 1),
                        else_=0,
                    ),
                    func.count(User.id).desc(),
                )
            )
            blocks_data = query.all()
            results = []
            for block in blocks_data:
                results.append({
                    'id': block.id,
                    'name': block.block_name,
                    'user_count': block.block_count,
                    'state_id': state_id,
                    'district_id': district_id
                })
            return results
        except Exception as ex:
            # error_logger.error(f"Error retriving user_course : {ex}")
            raise ex
