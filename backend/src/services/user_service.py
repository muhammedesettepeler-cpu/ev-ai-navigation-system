    """Handle user-related database operations."""

    def __init__(self) -> None:
        """Initialize user service with auth service instance."""
        self.auth_service = AuthService()

    async def create_user(
        self, email: str, password: str, username: Optional[str] = None
    ) -> Optional[Dict[str, any]]:
        """
        Create a new user account.

        Args:
            email: User's email address
            password: Plain text password
            username: Optional username

        Returns:
            User data dict if successful, None if user exists

        Raises:
            Exception: If database operation fails
        """
        async with AsyncSessionLocal() as session:
            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.warning(f"User registration failed: {email} already exists")
                return None

            # Hash password and create user
            password_hash = self.auth_service.hash_password(password)

            new_user = User(
                email=email,
                username=username or email.split("@")[0],
                password_hash=password_hash,
                is_active=True,
                created_at=datetime.utcnow(),
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            logger.info(f"New user created: {email}")

            return {
                "id": new_user.id,
                "email": new_user.email,
                "username": new_user.username,
                "created_at": new_user.created_at.isoformat(),
            }

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[Dict[str, any]]:
        """
        Authenticate user with email and password.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            User data with tokens if successful, None if authentication fails
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Login failed: user {email} not found")
                return None

            if not user.is_active:
                logger.warning(f"Login failed: user {email} is inactive")
                return None

            # Verify password
            if not self.auth_service.verify_password(password, user.password_hash):
                logger.warning(f"Login failed: incorrect password for {email}")
                return None

            # Update last login
            user.last_login = datetime.utcnow()
            await session.commit()

            # Generate tokens
            access_token = self.auth_service.create_access_token(user.id, user.email)
            refresh_token = self.auth_service.create_refresh_token(user.id)

            logger.info(f"User logged in: {email}")

            return {
                "user": {"id": user.id, "email": user.email, "username": user.username},
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, any]]:
        """
        Get user information by ID.

        Args:
            user_id: User's database ID

        Returns:
            User data dict if found, None otherwise
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "created_at": user.created_at.isoformat(),
                    "last_login": (
                        user.last_login.isoformat() if user.last_login else None
                    ),
                }
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token if successful, None if refresh token invalid
        """
        payload = self.auth_service.verify_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return None

        user_id = int(payload.get("sub"))
        user_data = await self.get_user_by_id(user_id)

        if not user_data:
            return None

        new_access_token = self.auth_service.create_access_token(
            user_id, user_data["email"]
        )

        return new_access_token
