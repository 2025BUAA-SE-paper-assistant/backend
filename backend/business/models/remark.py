from django.db import models
from django.conf import settings
from .paper import Paper
from .user import User
from django.db.models import Count


class Remark(models.Model):
    VISIBILITY_CHOICES = [
        ("private", "私有"),
        ("public", "公开"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="remarks"
    )
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="remarks")
    content = models.TextField()  # 标注内容
    paragraph_id = models.IntegerField()  # 段落编号
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="private"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        User, related_name="liked_remarks", blank=True
    )

    def like_count(self):
        return self.likes.count()

    def is_liked(self, user):
        return self.likes.filter(user_id=user.user_id).exists()

    def __str__(self):
        return f"Remark by {self.user.username} on {self.paper.title}"
