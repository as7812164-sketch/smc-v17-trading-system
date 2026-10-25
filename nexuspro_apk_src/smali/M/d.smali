.class abstract LM/d;
.super Ljava/lang/Object;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        LM/d$b;
    }
.end annotation


# static fields
.field private static final a:LM/c;


# direct methods
.method static constructor <clinit>()V
    .locals 1

    .line 1
    invoke-static {}, LM/d;->a()LM/c;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    sput-object v0, LM/d;->a:LM/c;

    .line 6
    .line 7
    return-void
.end method

.method private static a()LM/c;
    .locals 2

    .line 1
    new-instance v0, LM/d$b;

    .line 2
    .line 3
    const/4 v1, 0x0

    .line 4
    invoke-direct {v0, v1}, LM/d$b;-><init>(LM/d$a;)V

    .line 5
    .line 6
    .line 7
    return-object v0
.end method

.method static b(Ljava/lang/Object;)Ljava/lang/String;
    .locals 0

    .line 1
    invoke-static {p0}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    .line 2
    .line 3
    .line 4
    move-result-object p0

    .line 5
    return-object p0
.end method
