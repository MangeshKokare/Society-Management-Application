from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import random
import uuid
class Society(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    society_code = models.CharField(
        max_length=10,
        unique=True,
        editable=False
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_societies"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.society_code:
            self.society_code = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.society_code})"


class Apartment(models.Model):
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name="apartments"
    )

    block = models.CharField(max_length=20)
    flat_number = models.CharField(max_length=20)


    
class UserProfile(models.Model):

    ROLE_CHOICES = (
        ('resident', 'Resident'),
        ('guard', 'Guard'),
        ('guard_admin', 'Guard Admin'),   
        ('society_admin', 'Society Admin'),
        ('admin', 'Super Admin'),
        ('service_provider', 'Service Provider'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    society = models.ForeignKey(
        Society,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        indexes = [
            models.Index(fields=["role", "status"]),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Visitor(models.Model):
    VISITOR_TYPE = [
        ('guest', 'Guest'),
        ('delivery', 'Delivery'),
        ('service', 'Service Provider'),
        ('cab', 'Cab Driver'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'), 
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out')
    ]

    name = models.CharField(max_length=100)
    visitor_type = models.CharField(max_length=20, choices=VISITOR_TYPE)
    mobile = models.CharField(max_length=15)

    society = models.ForeignKey(
        'Society',
        on_delete=models.CASCADE
    )

    apartment = models.ForeignKey(
        'Apartment',
        on_delete=models.CASCADE,
        related_name="visitors"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # 🔐 ENTRY CODE - Unique 6-digit code
    entry_code = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        unique=True,
        db_index=True
    )
    code_expires_at = models.DateTimeField(null=True, blank=True)

    # 🕒 TIME TRACKING
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    # 👮 GUARD TRACKING
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_visitors'
    )
    
    checked_out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_out_visitors'
    )

    # ✅ RESIDENT APPROVAL TRACKING
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_visitors"
    )

    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_visitors"
    )
    purpose = models.TextField(blank=True)
    expected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate code when status is approved and code doesn't exist
        if self.status == "approved" and not self.entry_code:
            self.entry_code = self._generate_unique_code()
            self.code_expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_code():
        """Generate a unique 6-digit numeric entry code"""
        while True:
            code = f"{random.randint(100000, 999999)}"
            if not Visitor.objects.filter(entry_code=code).exists():
                return code

    def __str__(self):
        return f"{self.name} - {self.apartment.flat_number}"

    def get_status_display_icon(self):
        """Return status with icon"""
        icons = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'checked_in': '🟢',
            'checked_out': '🔴'
        }
        return f"{icons.get(self.status, '❓')} {self.get_status_display()}"

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['apartment', 'status']),
        ]

    


class Delivery(models.Model):
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE
    )

    company = models.CharField(max_length=100)
    tracking_id = models.CharField(max_length=100)

    otp = models.CharField(max_length=6)

    photo = models.ImageField(
        upload_to="deliveries/",
        null=True,
        blank=True
    )

    status = models.CharField(max_length=50)
    received_at = models.DateTimeField(null=True, blank=True)




class Service(models.Model):
    name = models.CharField(max_length=50)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DailyHelp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)

    timing = models.CharField(max_length=100)
    days = models.CharField(max_length=100)

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.service.name})"


class EmergencyContact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)


class Announcement(models.Model):
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name="announcements",
        null=True,  # Add temporarily for migration
        blank=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_announcements",
        null=True,  # Add temporarily for migration
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CommunityPost(models.Model):
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name="community_posts",
        null=True,  # Add temporarily for migration
        blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} post"

# Add this model to your models.py file

class PostLike(models.Model):
    """Track which users liked which posts - ensures one like per user"""
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='post_likes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='liked_posts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']  # Prevents duplicate likes
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"

class Comment(models.Model):
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="comments_list"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"


class Poll(models.Model):
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name="polls",
        null=True,  # Add temporarily for migration
        blank=True
    )
    question = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_polls",
        null=True,  # Add temporarily for migration
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, related_name="options", on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.text


class PollVote(models.Model):
    """Track who voted for what to prevent duplicate votes"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="poll_votes")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['poll', 'user']

    def __str__(self):
        return f"{self.user.username} voted on {self.poll.question}"



from django.contrib.auth.models import User

class Complaint(models.Model):

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications"
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]



class DailyHelpAttendance(models.Model):
    daily_help = models.ForeignKey(DailyHelp, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.DateTimeField(null=True)
    check_out = models.DateTimeField(null=True)


class EmergencyAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)


class ChildSafetyAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class Vendor(models.Model):
    society = models.ForeignKey(Society, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)


class Vehicle(models.Model):

    VEHICLE_TYPE_CHOICES = (
        ('2wheeler', 'Two Wheeler'),
        ('4wheeler', 'Four Wheeler'),
        ('bicycle', 'Bicycle'),
        ('truck', 'Truck'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name="vehicles"
    )

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES
    )

    registration_number = models.CharField(max_length=20)

    brand = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=30, blank=True)

    parking_slot = models.CharField(max_length=20, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("apartment", "registration_number")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.registration_number} ({self.apartment})"





class ServiceProvider(models.Model):
    """Service providers registered in the system (Maids, Drivers, Cooks, etc.)"""
    

    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="service_provider_profile",
        null=True,
        blank=True
    )
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE, 
        related_name='providers'
    )
    
    # Personal Details
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15)
    alternate_mobile = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField(null=True, blank=True)
    
    # Location Details
    area = models.CharField(max_length=200, help_text="e.g., Nanded City, Sinhagad Road")
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    full_address = models.TextField(blank=True)
    
    # Professional Details
    experience_years = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Verification
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS, 
        default='pending'
    )
    id_proof = models.ImageField(upload_to='service_providers/id_proof/', null=True, blank=True)
    photo = models.ImageField(upload_to='service_providers/photos/', null=True, blank=True)
    police_verification = models.BooleanField(default=False)
    
    # Availability
    available_days = models.CharField(
        max_length=200, 
        help_text="e.g., Mon-Fri, All Days"
    )
    preferred_timings = models.CharField(
        max_length=200, 
        help_text="e.g., 6 AM - 10 AM, Evening"
    )
    is_available = models.BooleanField(default=True)
    
    # Ratings & Reviews
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Stats
    total_hires = models.PositiveIntegerField(default=0)
    active_clients = models.PositiveIntegerField(default=0)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-rating', '-total_hires']
        indexes = [
            models.Index(fields=['area', 'city']),
            models.Index(fields=['service', 'verification_status']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.service.name} ({self.area})"


class HiredService(models.Model):
    """
    Track which residents have hired which service providers.
    Snapshot provider details at time of hire so old residents
    are not affected by future profile updates.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),        # Awaiting provider acceptance
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('terminated', 'Terminated'),
    ]

    # ================= RELATIONS =================
    resident = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hired_services'
    )

    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='clients'
    )

    # ================= SNAPSHOT (SAFE) =================
    provider_name = models.CharField(
        max_length=150,
        default="",
        blank=True
    )

    provider_mobile = models.CharField(
        max_length=15,
        default="",
        blank=True
    )

    provider_service = models.CharField(
        max_length=100,
        default="",
        blank=True
    )

    provider_area = models.CharField(
        max_length=100,
        default="",
        blank=True
    )

    provider_city = models.CharField(
        max_length=100,
        default="",
        blank=True
    )

    provider_preferred_timings = models.CharField(
        max_length=100,
        default="",
        blank=True
    )

    provider_available_days = models.CharField(
        max_length=100,
        default="",
        blank=True
    )

    provider_experience_years = models.PositiveIntegerField(
        default=0
    )

    provider_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )

    # ================= AGREED SERVICE DETAILS =================
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    timing = models.CharField(
        max_length=100,
        help_text="e.g., 6 AM - 8 AM"
    )

    days = models.CharField(
        max_length=100,
        help_text="e.g., Mon-Sat"
    )

    monthly_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # ================= NOTES =================
    special_instructions = models.TextField(blank=True)

    # ================= TIMESTAMPS =================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['resident', 'service_provider']

    def __str__(self):
        return f"{self.resident.username} hired {self.provider_name}"




class ServiceReview(models.Model):
    hired_service = models.OneToOneField(
        HiredService,
        on_delete=models.CASCADE,
        related_name='review'
    )
    rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )
    review_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



class PatrolRound(models.Model):
    """
    Track guard patrol rounds
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    guard = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='patrol_rounds'
    )
    
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name='patrol_rounds'
    )
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    checkpoints_completed = models.IntegerField(default=0)
    total_checkpoints = models.IntegerField(default=10)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def duration_minutes(self):
        """Calculate patrol duration in minutes"""
        if self.end_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() / 60)
        return 0
    
    def __str__(self):
        return f"Patrol by {self.guard.user.username} - {self.start_time.strftime('%d %b %Y, %I:%M %p')}"

class Checkpoint(models.Model):
    """
    Define checkpoints in society for patrol
    """
    CHECKPOINT_TYPES = [
        ('gate', 'Gate'),
        ('parking', 'Parking'),
        ('amenity', 'Amenity'),
        ('building', 'Building'),
        ('perimeter', 'Perimeter'),
    ]
    
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name='checkpoints'
    )
    
    name = models.CharField(max_length=100)
    checkpoint_type = models.CharField(max_length=20, choices=CHECKPOINT_TYPES)
    
    location_description = models.TextField()
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    
    icon = models.CharField(max_length=10, default='📍')
    
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # For ordering in patrol route
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.society.name}"


class CheckpointScan(models.Model):
    """
    Log each checkpoint scan during patrol
    """
    patrol_round = models.ForeignKey(
        PatrolRound,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    
    checkpoint = models.ForeignKey(
        Checkpoint,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    
    scanned_at = models.DateTimeField(auto_now_add=True)
    
    # Optional fields for detailed logging
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    photo = models.ImageField(
        upload_to='patrol_photos/',
        null=True,
        blank=True
    )
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['scanned_at']
        unique_together = ['patrol_round', 'checkpoint']
    
    def __str__(self):
        return f"{self.checkpoint.name} - {self.scanned_at.strftime('%I:%M %p')}"


class IncidentReport(models.Model):
    """
    Log security incidents reported by guards
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    INCIDENT_TYPES = [
        ('suspicious_activity', 'Suspicious Activity'),
        ('safety_hazard', 'Safety Hazard'),
        ('property_damage', 'Property Damage'),
        ('medical_emergency', 'Medical Emergency'),
        ('fire', 'Fire'),
        ('theft', 'Theft'),
        ('disturbance', 'Disturbance'),
        ('maintenance', 'Maintenance Issue'),
        ('other', 'Other'),
    ]
    
    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reported_incidents'
    )
    
    patrol_round = models.ForeignKey(
        PatrolRound,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents'
    )
    
    incident_type = models.CharField(
        max_length=30,
        choices=INCIDENT_TYPES
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='medium'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='reported'
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    location = models.CharField(max_length=200)
    
    # Optional GPS coordinates
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Evidence
    photo1 = models.ImageField(upload_to='incidents/', null=True, blank=True)
    photo2 = models.ImageField(upload_to='incidents/', null=True, blank=True)
    photo3 = models.ImageField(upload_to='incidents/', null=True, blank=True)
    
    # Timestamps
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Response
    action_taken = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_incidents'
    )
    
    class Meta:
        ordering = ['-reported_at']
    
    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.reported_at.strftime('%d %b %Y')}"


class GuardShift(models.Model):
    """
    Track guard shift schedules
    """

    SHIFT_TYPES = [
        ('morning', 'Morning (6 AM - 2 PM)'),
        ('afternoon', 'Afternoon (2 PM - 10 PM)'),
        ('night', 'Night (10 PM - 6 AM)'),
    ]

    SHIFT_STATUS = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ]
    ATTENDANCE_OVERRIDE = [
        ('auto', 'Auto (System)'),
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave'),
    ]

    guard = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='shifts'
    )

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name='guard_shifts'
    )
    shift_name = models.CharField(max_length=100, blank=True) 
    date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES)

    status = models.CharField(
        max_length=20,
        choices=SHIFT_STATUS,
        default='scheduled'
    )

    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    # Attendance override by guard_admin
    attendance_override = models.CharField(
        max_length=10,
        choices=ATTENDANCE_OVERRIDE,
        default='auto'
    )

    attendance_marked_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='attendance_marked_shifts'
    )

    attendance_marked_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_present = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    assigned_checkpoints = models.ManyToManyField(
        Checkpoint, 
        blank=True,
        related_name='assigned_shifts'
    )
    class Meta:
        ordering = ['-date', 'shift_type']
        unique_together = ['guard', 'date', 'shift_type']

    def get_duration(self):
        """Calculate shift duration in hours and minutes"""
        if self.check_in and self.check_out:
            duration = self.check_out - self.check_in
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            return f"{hours}h {minutes}m"
        return "—"
    def __str__(self):
        return f"{self.guard.user.username} - {self.date} {self.get_shift_type_display()}"



class VisitorPhoto(models.Model):
    """
    Store visitor photos taken by guards
    """
    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    
    photo = models.ImageField(upload_to='visitor_photos/')
    taken_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    taken_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-taken_at']
    
    def __str__(self):
        return f"Photo of {self.visitor.name} - {self.taken_at.strftime('%d %b %Y')}"


class DeliveryPhoto(models.Model):
    """
    Store delivery/parcel photos
    """
    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    
    photo = models.ImageField(upload_to='delivery_photos/')
    taken_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    taken_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-taken_at']
    
    def __str__(self):
        return f"Photo of delivery {self.delivery.tracking_id}"











class LeaveRequest(models.Model):
    """Guard leave request model"""
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('emergency', 'Emergency Leave'),
        ('vacation', 'Vacation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    guard = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='leave_requests')
    society = models.ForeignKey('Society', on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.guard.user.username} - {self.leave_type} ({self.start_date} to {self.end_date})"
    
    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1


class GuardAdminChat(models.Model):
    """Chat messages between guard and admin"""
    MESSAGE_TYPES = [
        ('leave_request', 'Leave Request'),
        ('general', 'General Chat'),
        ('complaint', 'Complaint'),
        ('query', 'Query'),
    ]
    
    society = models.ForeignKey('Society', on_delete=models.CASCADE)
    guard = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='guard_chats')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_guard_chats')
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='general')
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.guard.user.username} - {self.created_at}"








# Add these models to your existing models.py file

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ChatRoom(models.Model):
    """
    Represents a chat conversation between two users
    """
    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chatrooms_as_user1'
    )
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chatrooms_as_user2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"
    
    def get_other_user(self, current_user):
        """Get the other participant in the chat"""
        return self.user2 if self.user1 == current_user else self.user1
    
    def get_unread_count(self, user):
        """Get count of unread messages for a user"""
        return self.messages.filter(
            sender=self.get_other_user(user),
            is_read=False
        ).count()
    
    def get_last_message(self):
        """Get the most recent message in the chat"""
        return self.messages.order_by('-created_at').first()


class ChatMessage(models.Model):
    """
    Individual messages in a chat conversation
    WhatsApp-like delivery and read status
    """
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    )
    
    chatroom = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='sent'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.message[:50]}"
    
    def mark_as_delivered(self):
        """Mark message as delivered (double tick gray)"""
        if self.status == 'sent':
            self.status = 'delivered'
            self.save(update_fields=['status'])
    
    def mark_as_read(self):
        """Mark message as read (double tick blue)"""
        if not self.is_read:
            self.is_read = True
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'status', 'read_at'])


class UserOnlineStatus(models.Model):
    """
    Track user online/offline status
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='online_status'
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "User Online Statuses"
    
    def __str__(self):
        status = "Online" if self.is_online else f"Last seen {self.last_seen}"
        return f"{self.user.username} - {status}"



class Bill(models.Model):
    """
    Bills and fines created by society_admin for residents/guards
    """
    CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('fine', 'Fine'),
        ('utility', 'Utility'),
        ('parking', 'Parking'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]

    society = models.ForeignKey(
        Society,
        on_delete=models.CASCADE,
        related_name='bills'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_bills'
    )

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.society.name})"

    def update_status(self):
        """Auto-update bill status based on payer payments and due date"""
        from django.utils import timezone
        payers = self.billpayer_set.all()
        if payers.exists() and payers.filter(status='pending').count() == 0:
            self.status = 'paid'
        elif self.due_date < timezone.now().date() and payers.filter(status='pending').exists():
            self.status = 'overdue'
        else:
            self.status = 'pending'
        self.save(update_fields=['status'])

    def get_category_display_icon(self):
        icons = {
            'maintenance': '🔧',
            'fine': '⚠️',
            'utility': '💡',
            'parking': '🅿️',
            'other': '📋',
        }
        return f"{icons.get(self.category, '📋')} {self.get_category_display()}"


class BillPayer(models.Model):
    """
    Individual payer entry for each Bill — one row per assigned user
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name='billpayer_set'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bill_payments'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    paid_at = models.DateTimeField(null=True, blank=True)

    # Optional: payment reference / transaction ID
    payment_reference = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ['bill', 'user']  # one row per user per bill

    def __str__(self):
        return f"{self.user.username} — {self.bill.title} ({self.status})"

    def mark_paid(self, reference=''):
        from django.utils import timezone
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.payment_reference = reference
        self.save()
        self.bill.update_status()