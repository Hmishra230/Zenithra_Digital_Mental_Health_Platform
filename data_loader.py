import json
import random
from datetime import datetime, timedelta
from typing import List, Dict

class ConversationDataLoader:
    def __init__(self, conversations_file='data/conversations.json'):
        self.conversations_file = conversations_file
    
    def load_conversations(self) -> List[Dict]:
        """Load conversations from JSON file"""
        try:
            with open(self.conversations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"⚠️ Conversation file {self.conversations_file} not found")
            return []
        except json.JSONDecodeError:
            print(f"⚠️ Error parsing JSON in {self.conversations_file}")
            return []
    
    def create_sample_conversations(self, students, num_conversations_per_student=2):
        """Create sample conversations for students using JSON data"""
        conversations_data = self.load_conversations()
        if not conversations_data:
            print("No conversation data loaded")
            return []
        
        sample_conversations = []
        
        for student in students[:min(len(students), 10)]:  # Limit to first 10 students
            # Randomly select conversations for this student
            selected_convos = random.sample(
                conversations_data, 
                min(num_conversations_per_student, len(conversations_data))
            )
            
            for convo_data in selected_convos:
                # Create conversation with random timestamp
                conversation = {
                    'student_id': student.id,
                    'user_message': convo_data['user_message'],
                    'bot_response': convo_data['bot_response'],
                    'crisis_detected': convo_data.get('crisis_detected', False),
                    'sentiment_score': convo_data.get('sentiment_score', 0.0),
                    'response_time': convo_data.get('response_time', 1.0),
                    'timestamp': datetime.utcnow() - timedelta(
                        hours=random.randint(1, 168),  # Random time in last week
                        minutes=random.randint(0, 59)
                    )
                }
                sample_conversations.append(conversation)
        
        return sample_conversations
    
    def add_conversations_to_db(self, db, ChatConversation, students):
        """Add conversations from JSON to database"""
        conversations = self.create_sample_conversations(students)
        
        for convo_data in conversations:
            conversation = ChatConversation(**convo_data)
            db.session.add(conversation)
        
        print(f"✅ Created {len(conversations)} conversations from JSON data")
        return len(conversations)

    def get_conversation_by_category(self, category: str) -> List[Dict]:
        """Get conversations filtered by category"""
        all_conversations = self.load_conversations()
        return [
            convo for convo in all_conversations 
            if convo.get('category', '').lower() == category.lower()
        ]
    
    def get_crisis_conversations(self) -> List[Dict]:
        """Get only crisis-related conversations"""
        all_conversations = self.load_conversations()
        return [
            convo for convo in all_conversations 
            if convo.get('crisis_detected', False)
        ]
