.class public LK/I;
.super Ljava/lang/Object;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        LK/I$a;,
        LK/I$b;
    }
.end annotation


# static fields
.field public static final j:LK/I$a;

.field public static final k:LK/I$a;


# instance fields
.field private a:Landroid/content/Context;

.field private final b:Ljava/lang/String;

.field private final c:I

.field private final d:I

.field private e:LK/I$b;

.field private f:Ln/f;

.field private g:Lo/m;

.field private h:Z

.field private i:J


# direct methods
.method static constructor <clinit>()V
    .locals 1

    .line 1
    new-instance v0, LK/D;

    .line 2
    .line 3
    invoke-direct {v0}, LK/D;-><init>()V

    .line 4
    .line 5
    .line 6
    sput-object v0, LK/I;->j:LK/I$a;

    .line 7
    .line 8
    new-instance v0, LK/E;

    .line 9
    .line 10
    invoke-direct {v0}, LK/E;-><init>()V

    .line 11
    .line 12
    .line 13
    sput-object v0, LK/I;->k:LK/I$a;

    .line 14
    .line 15
    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Ljava/lang/String;Ljava/lang/Integer;Lo/m;)V
    .locals 0

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    iput-object p1, p0, LK/I;->a:Landroid/content/Context;

    .line 5
    .line 6
    invoke-virtual {p3}, Ljava/lang/Integer;->intValue()I

    .line 7
    .line 8
    .line 9
    move-result p3

    .line 10
    iput p3, p0, LK/I;->d:I

    .line 11
    .line 12
    iput-object p4, p0, LK/I;->g:Lo/m;

    .line 13
    .line 14
    if-nez p2, :cond_0

    .line 15
    .line 16
    invoke-virtual {p1}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 17
    .line 18
    .line 19
    move-result-object p1

    .line 20
    invoke-static {p1}, LK/J;->b(Landroid/content/pm/PackageManager;)LK/J$a;

    .line 21
    .line 22
    .line 23
    move-result-object p1

    .line 24
    iget-object p2, p1, LK/J$a;->b:Ljava/lang/String;

    .line 25
    .line 26
    iput-object p2, p0, LK/I;->b:Ljava/lang/String;

    .line 27
    .line 28
    iget p1, p1, LK/J$a;->a:I

    .line 29
    .line 30
    iput p1, p0, LK/I;->c:I

    .line 31
    .line 32
    return-void

    .line 33
    :cond_0
    iput-object p2, p0, LK/I;->b:Ljava/lang/String;

    .line 34
    .line 35
    const/4 p1, 0x0

    .line 36
    iput p1, p0, LK/I;->c:I

    .line 37
    .line 38
    return-void
.end method

.method public static synthetic a(LK/I;Lo/q;LL/e;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2, p3}, LK/I;->o(Lo/q;LL/e;Ljava/lang/Runnable;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method public static synthetic b(LK/I;LK/I$a;Lo/q;Ljava/lang/Runnable;)V
    .locals 1

    .line 1
    iget-object v0, p0, LK/I;->a:Landroid/content/Context;

    .line 2
    .line 3
    iget-object p0, p0, LK/I;->b:Ljava/lang/String;

    .line 4
    .line 5
    invoke-interface {p1, v0, p2, p0, p3}, LK/I$a;->a(Landroid/content/Context;Lo/q;Ljava/lang/String;Ljava/lang/Runnable;)V

    .line 6
    .line 7
    .line 8
    return-void
.end method

.method public static synthetic c(Landroid/content/Context;Lo/q;Ljava/lang/String;Ljava/lang/Runnable;)V
    .locals 3

    .line 1
    invoke-virtual {p1}, Lo/q;->b()Ln/d;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    if-eqz p2, :cond_0

    .line 6
    .line 7
    iget-object v1, v0, Ln/d;->a:Landroid/content/Intent;

    .line 8
    .line 9
    invoke-virtual {v1, p2}, Landroid/content/Intent;->setPackage(Ljava/lang/String;)Landroid/content/Intent;

    .line 10
    .line 11
    .line 12
    :cond_0
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 13
    .line 14
    .line 15
    move-result-object p2

    .line 16
    invoke-static {p2}, LK/c;->a(Landroid/content/pm/PackageManager;)Z

    .line 17
    .line 18
    .line 19
    move-result p2

    .line 20
    if-eqz p2, :cond_1

    .line 21
    .line 22
    iget-object p2, v0, Ln/d;->a:Landroid/content/Intent;

    .line 23
    .line 24
    const-string v1, "android.support.customtabs.extra.LAUNCH_AS_TRUSTED_WEB_ACTIVITY"

    .line 25
    .line 26
    const/4 v2, 0x1

    .line 27
    invoke-virtual {p2, v1, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Z)Landroid/content/Intent;

    .line 28
    .line 29
    .line 30
    :cond_1
    invoke-virtual {p1}, Lo/q;->c()Landroid/net/Uri;

    .line 31
    .line 32
    .line 33
    move-result-object p1

    .line 34
    invoke-virtual {v0, p0, p1}, Ln/d;->c(Landroid/content/Context;Landroid/net/Uri;)V

    .line 35
    .line 36
    .line 37
    if-eqz p3, :cond_2

    .line 38
    .line 39
    invoke-interface {p3}, Ljava/lang/Runnable;->run()V

    .line 40
    .line 41
    .line 42
    :cond_2
    return-void
.end method

.method public static synthetic d(LK/I;Lo/q;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2}, LK/I;->p(Lo/q;Ljava/lang/Runnable;)V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method public static synthetic e(Landroid/content/Context;Lo/q;Ljava/lang/String;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    invoke-virtual {p1}, Lo/q;->c()Landroid/net/Uri;

    .line 2
    .line 3
    .line 4
    move-result-object p1

    .line 5
    invoke-static {p0}, LK/i;->d(Landroid/content/Context;)LK/i;

    .line 6
    .line 7
    .line 8
    move-result-object p2

    .line 9
    invoke-static {p0, p1, p2}, Lcom/google/androidbrowserhelper/trusted/WebViewFallbackActivity;->h(Landroid/content/Context;Landroid/net/Uri;LK/i;)Landroid/content/Intent;

    .line 10
    .line 11
    .line 12
    move-result-object p1

    .line 13
    invoke-virtual {p0, p1}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V

    .line 14
    .line 15
    .line 16
    if-eqz p3, :cond_0

    .line 17
    .line 18
    invoke-interface {p3}, Ljava/lang/Runnable;->run()V

    .line 19
    .line 20
    .line 21
    :cond_0
    return-void
.end method

.method static synthetic f(LK/I;)Landroid/content/Context;
    .locals 0

    .line 1
    iget-object p0, p0, LK/I;->a:Landroid/content/Context;

    .line 2
    .line 3
    return-object p0
.end method

.method static synthetic g(LK/I;)Ljava/lang/String;
    .locals 0

    .line 1
    iget-object p0, p0, LK/I;->b:Ljava/lang/String;

    .line 2
    .line 3
    return-object p0
.end method

.method static synthetic h(LK/I;)Ln/f;
    .locals 0

    .line 1
    iget-object p0, p0, LK/I;->f:Ln/f;

    .line 2
    .line 3
    return-object p0
.end method

.method static synthetic i(LK/I;Ln/f;)Ln/f;
    .locals 0

    .line 1
    iput-object p1, p0, LK/I;->f:Ln/f;

    .line 2
    .line 3
    return-object p1
.end method

.method static synthetic j(LK/I;)I
    .locals 0

    .line 1
    iget p0, p0, LK/I;->d:I

    .line 2
    .line 3
    return p0
.end method

.method private n(Lo/q;Ln/b;LL/e;Ljava/lang/Runnable;LK/I$a;)V
    .locals 1

    .line 1
    if-eqz p3, :cond_0

    .line 2
    .line 3
    iget-object v0, p0, LK/I;->b:Ljava/lang/String;

    .line 4
    .line 5
    invoke-interface {p3, v0, p1}, LL/e;->a(Ljava/lang/String;Lo/q;)V

    .line 6
    .line 7
    .line 8
    :cond_0
    new-instance v0, LK/F;

    .line 9
    .line 10
    invoke-direct {v0, p0, p1, p3, p4}, LK/F;-><init>(LK/I;Lo/q;LL/e;Ljava/lang/Runnable;)V

    .line 11
    .line 12
    .line 13
    iget-object p3, p0, LK/I;->f:Ln/f;

    .line 14
    .line 15
    if-eqz p3, :cond_1

    .line 16
    .line 17
    invoke-interface {v0}, Ljava/lang/Runnable;->run()V

    .line 18
    .line 19
    .line 20
    return-void

    .line 21
    :cond_1
    new-instance p3, LK/G;

    .line 22
    .line 23
    invoke-direct {p3, p0, p5, p1, p4}, LK/G;-><init>(LK/I;LK/I$a;Lo/q;Ljava/lang/Runnable;)V

    .line 24
    .line 25
    .line 26
    iget-object p1, p0, LK/I;->e:LK/I$b;

    .line 27
    .line 28
    if-nez p1, :cond_2

    .line 29
    .line 30
    new-instance p1, LK/I$b;

    .line 31
    .line 32
    invoke-direct {p1, p0, p2}, LK/I$b;-><init>(LK/I;Ln/b;)V

    .line 33
    .line 34
    .line 35
    iput-object p1, p0, LK/I;->e:LK/I$b;

    .line 36
    .line 37
    :cond_2
    iget-object p1, p0, LK/I;->e:LK/I$b;

    .line 38
    .line 39
    invoke-static {p1, v0, p3}, LK/I$b;->c(LK/I$b;Ljava/lang/Runnable;Ljava/lang/Runnable;)V

    .line 40
    .line 41
    .line 42
    iget-object p1, p0, LK/I;->a:Landroid/content/Context;

    .line 43
    .line 44
    iget-object p2, p0, LK/I;->b:Ljava/lang/String;

    .line 45
    .line 46
    iget-object p3, p0, LK/I;->e:LK/I$b;

    .line 47
    .line 48
    invoke-static {p1, p2, p3}, Ln/c;->b(Landroid/content/Context;Ljava/lang/String;Ln/e;)Z

    .line 49
    .line 50
    .line 51
    return-void
.end method

.method private o(Lo/q;LL/e;Ljava/lang/Runnable;)V
    .locals 2

    .line 1
    iget-object v0, p0, LK/I;->f:Ln/f;

    .line 2
    .line 3
    if-eqz v0, :cond_1

    .line 4
    .line 5
    if-eqz p2, :cond_0

    .line 6
    .line 7
    new-instance v1, LK/H;

    .line 8
    .line 9
    invoke-direct {v1, p0, p1, p3}, LK/H;-><init>(LK/I;Lo/q;Ljava/lang/Runnable;)V

    .line 10
    .line 11
    .line 12
    invoke-interface {p2, p1, v0, v1}, LL/e;->b(Lo/q;Ln/f;Ljava/lang/Runnable;)V

    .line 13
    .line 14
    .line 15
    return-void

    .line 16
    :cond_0
    invoke-direct {p0, p1, p3}, LK/I;->p(Lo/q;Ljava/lang/Runnable;)V

    .line 17
    .line 18
    .line 19
    return-void

    .line 20
    :cond_1
    new-instance p1, Ljava/lang/IllegalStateException;

    .line 21
    .line 22
    const-string p2, "mSession is null in launchWhenSessionEstablished"

    .line 23
    .line 24
    invoke-direct {p1, p2}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    .line 25
    .line 26
    .line 27
    throw p1
.end method

.method private p(Lo/q;Ljava/lang/Runnable;)V
    .locals 4

    .line 1
    iget-boolean v0, p0, LK/I;->h:Z

    .line 2
    .line 3
    if-nez v0, :cond_2

    .line 4
    .line 5
    iget-object v0, p0, LK/I;->f:Ln/f;

    .line 6
    .line 7
    if-nez v0, :cond_0

    .line 8
    .line 9
    goto :goto_0

    .line 10
    :cond_0
    const-string v0, "TwaLauncher"

    .line 11
    .line 12
    const-string v1, "Launching Trusted Web Activity."

    .line 13
    .line 14
    invoke-static {v0, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 15
    .line 16
    .line 17
    iget-object v0, p0, LK/I;->f:Ln/f;

    .line 18
    .line 19
    invoke-virtual {p1, v0}, Lo/q;->a(Ln/f;)Lo/p;

    .line 20
    .line 21
    .line 22
    move-result-object p1

    .line 23
    iget-wide v0, p0, LK/I;->i:J

    .line 24
    .line 25
    const-wide/16 v2, 0x0

    .line 26
    .line 27
    cmp-long v0, v0, v2

    .line 28
    .line 29
    if-eqz v0, :cond_1

    .line 30
    .line 31
    invoke-virtual {p1}, Lo/p;->a()Landroid/content/Intent;

    .line 32
    .line 33
    .line 34
    move-result-object v0

    .line 35
    const-string v1, "org.chromium.chrome.browser.customtabs.trusted.STARTUP_UPTIME_MILLIS"

    .line 36
    .line 37
    iget-wide v2, p0, LK/I;->i:J

    .line 38
    .line 39
    invoke-virtual {v0, v1, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;J)Landroid/content/Intent;

    .line 40
    .line 41
    .line 42
    :cond_1
    invoke-virtual {p1}, Lo/p;->a()Landroid/content/Intent;

    .line 43
    .line 44
    .line 45
    move-result-object v0

    .line 46
    const-string v1, "org.chromium.chrome.browser.ANDROID_BROWSER_HELPER_VERSION"

    .line 47
    .line 48
    const/4 v2, 0x2

    .line 49
    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;

    .line 50
    .line 51
    .line 52
    invoke-virtual {p1}, Lo/p;->a()Landroid/content/Intent;

    .line 53
    .line 54
    .line 55
    move-result-object v0

    .line 56
    iget-object v1, p0, LK/I;->a:Landroid/content/Context;

    .line 57
    .line 58
    invoke-static {v0, v1}, Lcom/google/androidbrowserhelper/trusted/FocusActivity;->a(Landroid/content/Intent;Landroid/content/Context;)V

    .line 59
    .line 60
    .line 61
    iget-object v0, p0, LK/I;->a:Landroid/content/Context;

    .line 62
    .line 63
    invoke-virtual {p1, v0}, Lo/p;->c(Landroid/content/Context;)V

    .line 64
    .line 65
    .line 66
    if-eqz p2, :cond_2

    .line 67
    .line 68
    invoke-interface {p2}, Ljava/lang/Runnable;->run()V

    .line 69
    .line 70
    .line 71
    :cond_2
    :goto_0
    return-void
.end method


# virtual methods
.method public k()V
    .locals 2

    .line 1
    iget-boolean v0, p0, LK/I;->h:Z

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget-object v0, p0, LK/I;->e:LK/I$b;

    .line 7
    .line 8
    if-eqz v0, :cond_1

    .line 9
    .line 10
    iget-object v1, p0, LK/I;->a:Landroid/content/Context;

    .line 11
    .line 12
    invoke-virtual {v1, v0}, Landroid/content/Context;->unbindService(Landroid/content/ServiceConnection;)V

    .line 13
    .line 14
    .line 15
    :cond_1
    const/4 v0, 0x0

    .line 16
    iput-object v0, p0, LK/I;->a:Landroid/content/Context;

    .line 17
    .line 18
    const/4 v0, 0x1

    .line 19
    iput-boolean v0, p0, LK/I;->h:Z

    .line 20
    .line 21
    return-void
.end method

.method public l()Ljava/lang/String;
    .locals 1

    .line 1
    iget-object v0, p0, LK/I;->b:Ljava/lang/String;

    .line 2
    .line 3
    return-object v0
.end method

.method public m(Lo/q;Ln/b;LL/e;Ljava/lang/Runnable;LK/I$a;)V
    .locals 1

    .line 1
    iget-boolean v0, p0, LK/I;->h:Z

    .line 2
    .line 3
    if-nez v0, :cond_2

    .line 4
    .line 5
    iget v0, p0, LK/I;->c:I

    .line 6
    .line 7
    if-nez v0, :cond_0

    .line 8
    .line 9
    invoke-direct/range {p0 .. p5}, LK/I;->n(Lo/q;Ln/b;LL/e;Ljava/lang/Runnable;LK/I$a;)V

    .line 10
    .line 11
    .line 12
    move-object p1, p0

    .line 13
    goto :goto_0

    .line 14
    :cond_0
    move-object p2, p1

    .line 15
    move-object p1, p0

    .line 16
    iget-object p3, p1, LK/I;->a:Landroid/content/Context;

    .line 17
    .line 18
    iget-object v0, p1, LK/I;->b:Ljava/lang/String;

    .line 19
    .line 20
    invoke-interface {p5, p3, p2, v0, p4}, LK/I$a;->a(Landroid/content/Context;Lo/q;Ljava/lang/String;Ljava/lang/Runnable;)V

    .line 21
    .line 22
    .line 23
    :goto_0
    iget-object p2, p1, LK/I;->a:Landroid/content/Context;

    .line 24
    .line 25
    invoke-virtual {p2}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 26
    .line 27
    .line 28
    move-result-object p2

    .line 29
    invoke-static {p2}, LK/c;->a(Landroid/content/pm/PackageManager;)Z

    .line 30
    .line 31
    .line 32
    move-result p2

    .line 33
    if-nez p2, :cond_1

    .line 34
    .line 35
    iget-object p2, p1, LK/I;->g:Lo/m;

    .line 36
    .line 37
    iget-object p3, p1, LK/I;->b:Ljava/lang/String;

    .line 38
    .line 39
    iget-object p4, p1, LK/I;->a:Landroid/content/Context;

    .line 40
    .line 41
    invoke-virtual {p4}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 42
    .line 43
    .line 44
    move-result-object p4

    .line 45
    invoke-static {p3, p4}, Lo/j;->a(Ljava/lang/String;Landroid/content/pm/PackageManager;)Lo/j;

    .line 46
    .line 47
    .line 48
    move-result-object p3

    .line 49
    invoke-interface {p2, p3}, Lo/m;->b(Lo/j;)V

    .line 50
    .line 51
    .line 52
    :cond_1
    return-void

    .line 53
    :cond_2
    move-object p1, p0

    .line 54
    new-instance p2, Ljava/lang/IllegalStateException;

    .line 55
    .line 56
    const-string p3, "TwaLauncher already destroyed"

    .line 57
    .line 58
    invoke-direct {p2, p3}, Ljava/lang/IllegalStateException;-><init>(Ljava/lang/String;)V

    .line 59
    .line 60
    .line 61
    throw p2
.end method

.method public q(J)V
    .locals 0

    .line 1
    iput-wide p1, p0, LK/I;->i:J

    .line 2
    .line 3
    return-void
.end method
