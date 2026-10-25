.class LK/I$b;
.super Ln/e;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = LK/I;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x2
    name = "b"
.end annotation


# instance fields
.field private b:Ljava/lang/Runnable;

.field private c:Ljava/lang/Runnable;

.field private d:Ln/b;

.field final synthetic e:LK/I;


# direct methods
.method constructor <init>(LK/I;Ln/b;)V
    .locals 0

    .line 1
    iput-object p1, p0, LK/I$b;->e:LK/I;

    .line 2
    .line 3
    invoke-direct {p0}, Ln/e;-><init>()V

    .line 4
    .line 5
    .line 6
    iput-object p2, p0, LK/I$b;->d:Ln/b;

    .line 7
    .line 8
    return-void
.end method

.method static synthetic c(LK/I$b;Ljava/lang/Runnable;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2}, LK/I$b;->d(Ljava/lang/Runnable;Ljava/lang/Runnable;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method private d(Ljava/lang/Runnable;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    iput-object p1, p0, LK/I$b;->b:Ljava/lang/Runnable;

    .line 2
    .line 3
    iput-object p2, p0, LK/I$b;->c:Ljava/lang/Runnable;

    .line 4
    .line 5
    return-void
.end method


# virtual methods
.method public a(Landroid/content/ComponentName;Ln/c;)V
    .locals 2

    .line 1
    iget-object p1, p0, LK/I$b;->e:LK/I;

    .line 2
    .line 3
    invoke-static {p1}, LK/I;->f(LK/I;)Landroid/content/Context;

    .line 4
    .line 5
    .line 6
    move-result-object p1

    .line 7
    invoke-virtual {p1}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 8
    .line 9
    .line 10
    move-result-object p1

    .line 11
    iget-object v0, p0, LK/I$b;->e:LK/I;

    .line 12
    .line 13
    invoke-static {v0}, LK/I;->g(LK/I;)Ljava/lang/String;

    .line 14
    .line 15
    .line 16
    move-result-object v0

    .line 17
    invoke-static {p1, v0}, LK/b;->c(Landroid/content/pm/PackageManager;Ljava/lang/String;)Z

    .line 18
    .line 19
    .line 20
    move-result p1

    .line 21
    if-nez p1, :cond_0

    .line 22
    .line 23
    const-wide/16 v0, 0x0

    .line 24
    .line 25
    invoke-virtual {p2, v0, v1}, Ln/c;->h(J)Z

    .line 26
    .line 27
    .line 28
    :cond_0
    :try_start_0
    iget-object p1, p0, LK/I$b;->e:LK/I;

    .line 29
    .line 30
    iget-object v0, p0, LK/I$b;->d:Ln/b;

    .line 31
    .line 32
    invoke-static {p1}, LK/I;->j(LK/I;)I

    .line 33
    .line 34
    .line 35
    move-result v1

    .line 36
    invoke-virtual {p2, v0, v1}, Ln/c;->f(Ln/b;I)Ln/f;

    .line 37
    .line 38
    .line 39
    move-result-object p2

    .line 40
    invoke-static {p1, p2}, LK/I;->i(LK/I;Ln/f;)Ln/f;

    .line 41
    .line 42
    .line 43
    iget-object p1, p0, LK/I$b;->e:LK/I;

    .line 44
    .line 45
    invoke-static {p1}, LK/I;->h(LK/I;)Ln/f;

    .line 46
    .line 47
    .line 48
    move-result-object p1

    .line 49
    if-eqz p1, :cond_1

    .line 50
    .line 51
    iget-object p1, p0, LK/I$b;->b:Ljava/lang/Runnable;

    .line 52
    .line 53
    if-eqz p1, :cond_1

    .line 54
    .line 55
    invoke-interface {p1}, Ljava/lang/Runnable;->run()V

    .line 56
    .line 57
    .line 58
    goto :goto_1

    .line 59
    :catch_0
    move-exception p1

    .line 60
    goto :goto_0

    .line 61
    :cond_1
    iget-object p1, p0, LK/I$b;->e:LK/I;

    .line 62
    .line 63
    invoke-static {p1}, LK/I;->h(LK/I;)Ln/f;

    .line 64
    .line 65
    .line 66
    move-result-object p1

    .line 67
    if-nez p1, :cond_2

    .line 68
    .line 69
    iget-object p1, p0, LK/I$b;->c:Ljava/lang/Runnable;

    .line 70
    .line 71
    if-eqz p1, :cond_2

    .line 72
    .line 73
    invoke-interface {p1}, Ljava/lang/Runnable;->run()V
    :try_end_0
    .catch Ljava/lang/RuntimeException; {:try_start_0 .. :try_end_0} :catch_0

    .line 74
    .line 75
    .line 76
    goto :goto_1

    .line 77
    :goto_0
    const-string p2, "TwaLauncher"

    .line 78
    .line 79
    invoke-static {p2, p1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 80
    .line 81
    .line 82
    iget-object p1, p0, LK/I$b;->c:Ljava/lang/Runnable;

    .line 83
    .line 84
    invoke-interface {p1}, Ljava/lang/Runnable;->run()V

    .line 85
    .line 86
    .line 87
    :cond_2
    :goto_1
    const/4 p1, 0x0

    .line 88
    iput-object p1, p0, LK/I$b;->b:Ljava/lang/Runnable;

    .line 89
    .line 90
    iput-object p1, p0, LK/I$b;->c:Ljava/lang/Runnable;

    .line 91
    .line 92
    return-void
.end method

.method public onServiceDisconnected(Landroid/content/ComponentName;)V
    .locals 1

    .line 1
    iget-object p1, p0, LK/I$b;->e:LK/I;

    .line 2
    .line 3
    const/4 v0, 0x0

    .line 4
    invoke-static {p1, v0}, LK/I;->i(LK/I;Ln/f;)Ln/f;

    .line 5
    .line 6
    .line 7
    return-void
.end method
