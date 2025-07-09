# 🔗 ChamaLink - Digital Chama Management Platform

ChamaLink is a comprehensive digital platform for managing Chama (investment groups) in Kenya and beyond. Built with Flask and modern web technologies, it provides a complete suite of tools for group financial management, member coordination, and administrative oversight.

## ✨ Key Features

### 🏦 **Core Chama Management**
- **Member Management**: Add, manage, and track chama members
- **Financial Tracking**: Record contributions, loans, and transactions
- **Meeting Coordination**: Schedule and manage group meetings
- **Secretary Tools**: Meeting minutes creation and management
- **Loan Management**: Track member loans and repayments

### 💰 **Financial Features**
- **M-Pesa Integration**: Automated payment processing
- **Transaction History**: Comprehensive financial records
- **Receipt Generation**: Digital receipts for all transactions
- **Recurring Payments**: Automated contribution scheduling
- **Multi-signature Transactions**: Enhanced security for large transactions

### 👑 **Administrative Features**
- **Admin Dashboard**: Comprehensive group management
- **Meeting Management**: Schedule, notify, and track meetings
- **Announcements**: Group-wide communication system
- **Notifications**: In-app and email notification system
- **Member Analytics**: Insights into group performance

### 🔐 **Security & Authentication**
- **Two-Factor Authentication (2FA)**: Enhanced account security
- **Role-based Access Control**: Different permissions for admins, secretaries, and members
- **Session Management**: Secure login and session handling
- **Data Protection**: Encrypted sensitive information

### 📊 **Subscription Management**
- **Flexible Plans**: Basic, Classic, and Advanced subscription tiers
- **Multi-month Options**: Discounted longer-term subscriptions
- **Enterprise Solutions**: Custom solutions for large organizations
- **Trial Periods**: Free trial for new users

### 🤖 **AI-Powered Features**
- **LeeBot**: Intelligent chatbot for user assistance
- **Context-aware Help**: Smart help system with escalation
- **Automated Insights**: AI-powered financial insights

## 🚀 Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite/PostgreSQL with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login with 2FA support
- **Email**: Flask-Mail for notifications
- **Payments**: M-Pesa API integration
- **Migrations**: Flask-Migrate (Alembic)

## 📦 Installation

### Prerequisites
- Python 3.8+
- Git
- SQLite (for development) or PostgreSQL (for production)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/chamalink.git
   cd chamalink
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///chamalink.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@chamalink.com
```

### M-Pesa Configuration (Optional)
```env
MPESA_CONSUMER_KEY=your-mpesa-consumer-key
MPESA_CONSUMER_SECRET=your-mpesa-consumer-secret
MPESA_SHORTCODE=your-shortcode
MPESA_PASSKEY=your-passkey
```

## 🔧 Usage

### For Chama Administrators
1. Register and create your chama
2. Invite members via email
3. Set up contribution schedules
4. Manage meetings and announcements
5. Track financial activities

### For Chama Members
1. Join via invitation link
2. Make contributions
3. Apply for loans
4. View meeting minutes
5. Track personal financial history

### For Secretaries
1. Create and manage meeting minutes
2. Upload meeting documents
3. Send meeting notifications
4. Manage member communications

## 📱 Mobile Responsiveness

ChamaLink is fully responsive and works seamlessly on:
- 📱 Mobile phones
- 📱 Tablets
- 💻 Desktop computers
- 🖥️ Large screens

## 🔐 Security Features

- **Password Security**: Bcrypt hashing
- **Session Protection**: CSRF protection
- **Data Encryption**: Sensitive data encryption
- **Audit Logging**: Comprehensive activity logs
- **Access Controls**: Role-based permissions

## 🚀 Deployment

### Production Deployment
1. Set up PostgreSQL database
2. Configure production environment variables
3. Run database migrations
4. Deploy to your preferred platform (Heroku, AWS, etc.)

### Docker Deployment (Coming Soon)
```bash
docker build -t chamalink .
docker run -p 5000:5000 chamalink
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

**Bilford Bwire** - Founder & Lead Developer
- Email: bilfordbwire@gmail.com
- LinkedIn: [bilford-bwire](https://linkedin.com/in/bilford-bwire)

## 🐛 Issues & Support

- 🐛 Report bugs via [GitHub Issues](https://github.com/yourusername/chamalink/issues)
- 💬 Get help via LeeBot (built-in chatbot)
- 📧 Contact: support@chamalink.com

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Integration with more payment providers
- [ ] Multi-language support
- [ ] Automated investment suggestions
- [ ] Document management system

## 🙏 Acknowledgments

- Flask community for the excellent framework
- Bootstrap team for the UI framework
- Contributors and beta testers
- Kenyan chama communities for feedback

---

**Made with ❤️ in Kenya for the Chama community worldwide**

Visit us at: [www.chamalink.com](https://www.chamalink.com)